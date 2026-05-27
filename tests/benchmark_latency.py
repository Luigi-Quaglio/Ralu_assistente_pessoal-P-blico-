"""
Script de medição de latência do pipeline Ralu

Mede tempo de cada etapa:
- Whisper (transcription)
- LLM (classification + response)
- TTS (text-to-speech)
- Pipeline completo

Gera CSV e estatísticas para análise no TCC.
"""
import time
import json
import sys
import os
from pathlib import Path
from typing import Dict, List
import statistics
import csv

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ralu import Ralu
from src.config import settings


class LatencyBenchmark:
    """Realiza benchmark de latência do pipeline"""
    
    def __init__(self):
        self.ralu = Ralu()
        self.results: List[Dict] = []
    
    def measure_classification_only(self, text: str) -> Dict[str, float]:
        """Mede apenas o tempo de classificação (LLM)"""
        start = time.time()
        intent_result = self.ralu.classify(text)
        end = time.time()
        
        return {
            "classification_time": end - start,
            "intent": intent_result.intent.value,
            "confidence": intent_result.confidence
        }
    
    def measure_full_pipeline(self, text: str) -> Dict[str, float]:
        """Mede o pipeline completo (classificação + handler + TTS)"""
        timings = {}
        
        # Total
        start_total = time.time()
        
        # Classificação
        start_classify = time.time()
        intent_result = self.ralu.classify(text)
        end_classify = time.time()
        timings["classification_time"] = end_classify - start_classify
        
        # Processamento (handler)
        start_handler = time.time()
        from src.handlers import process_intent
        action_result = process_intent(intent_result)
        end_handler = time.time()
        timings["handler_time"] = end_handler - start_handler
        
        # Formatação
        start_format = time.time()
        from src.utils.response_formatter import format_result
        readable = format_result(action_result)
        end_format = time.time()
        timings["format_time"] = end_format - start_format
        
        # TTS (se habilitado)
        if settings.ralu_tts:
            start_tts = time.time()
            try:
                from src.utils import tts
                tts.speak(readable)
            except Exception as e:
                print(f"TTS falhou: {e}")
            end_tts = time.time()
            timings["tts_time"] = end_tts - start_tts
        else:
            timings["tts_time"] = 0.0
        
        end_total = time.time()
        timings["total_time"] = end_total - start_total
        
        # Metadados
        timings["intent"] = intent_result.intent.value
        timings["confidence"] = intent_result.confidence
        timings["text"] = text
        
        return timings
    
    def run_benchmark(self, test_phrases: List[str], iterations: int = 3):
        """Executa benchmark com múltiplas frases e iterações"""
        print(f"Executando benchmark com {len(test_phrases)} frases, {iterations} iterações cada...")
        print("=" * 70)
        
        total_tests = len(test_phrases) * iterations
        current = 0
        
        for phrase in test_phrases:
            for i in range(iterations):
                current += 1
                print(f"[{current}/{total_tests}] Testando: '{phrase[:50]}...'")
                
                try:
                    result = self.measure_full_pipeline(phrase)
                    result["iteration"] = i + 1
                    self.results.append(result)
                    
                    print(f"  ├─ Classificação: {result['classification_time']:.3f}s")
                    print(f"  ├─ Handler: {result['handler_time']:.3f}s")
                    print(f"  ├─ TTS: {result['tts_time']:.3f}s")
                    print(f"  └─ Total: {result['total_time']:.3f}s")
                    
                except Exception as e:
                    print(f"  └─ ERRO: {e}")
                
                # Pausa entre testes
                time.sleep(0.5)
            
            print()
    
    def calculate_statistics(self) -> Dict:
        """Calcula estatísticas agregadas"""
        if not self.results:
            return {}
        
        stats = {}
        metrics = ["classification_time", "handler_time", "tts_time", "total_time"]
        
        for metric in metrics:
            values = [r[metric] for r in self.results if metric in r]
            if values:
                stats[metric] = {
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "stdev": statistics.stdev(values) if len(values) > 1 else 0,
                    "min": min(values),
                    "max": max(values)
                }
        
        return stats
    
    def save_results(self, output_dir: Path = None):
        """Salva resultados em CSV e JSON"""
        if not output_dir:
            output_dir = Path(__file__).parent.parent / "data" / "benchmarks"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # CSV com resultados individuais
        csv_file = output_dir / f"latency_raw_{timestamp}.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            if self.results:
                writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
                writer.writeheader()
                writer.writerows(self.results)
        
        print(f"Resultados salvos em: {csv_file}")
        
        # JSON com estatísticas
        stats = self.calculate_statistics()
        json_file = output_dir / f"latency_stats_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"Estatísticas salvas em: {json_file}")
        
        return csv_file, json_file
    
    def print_report(self):
        """Imprime relatório consolidado"""
        stats = self.calculate_statistics()
        
        print("\n" + "=" * 70)
        print("RELATÓRIO DE LATÊNCIA DO PIPELINE")
        print("=" * 70)
        
        print(f"\nTotal de testes: {len(self.results)}")
        
        print("\n┌─────────────────────────┬─────────┬─────────┬─────────┬─────────┐")
        print("│ Etapa                   │  Média  │ Mediana │   Min   │   Max   │")
        print("├─────────────────────────┼─────────┼─────────┼─────────┼─────────┤")
        
        labels = {
            "classification_time": "Classificação (LLM)",
            "handler_time": "Handler",
            "tts_time": "TTS",
            "total_time": "TOTAL"
        }
        
        for metric, label in labels.items():
            if metric in stats:
                s = stats[metric]
                print(f"│ {label:23} │ {s['mean']:7.3f} │ {s['median']:7.3f} │ {s['min']:7.3f} │ {s['max']:7.3f} │")
        
        print("└─────────────────────────┴─────────┴─────────┴─────────┴─────────┘")
        print("\n(Todos os tempos em segundos)")
        
        # Tabela para TCC
        print("\n" + "=" * 70)
        print("TABELA PARA TCC (LaTeX)")
        print("=" * 70)
        print()
        print("| Etapa   | Tempo médio |")
        print("| ------- | ----------- |")
        for metric, label in labels.items():
            if metric in stats:
                s = stats[metric]
                short_label = label.split(" ")[0]
                print(f"| {short_label:7} | {s['mean']:6.2f} s    |")


def main():
    """Função principal"""
    # Frases de teste representativas
    test_phrases = [
        "Adiciona um evento amanhã às 14 horas reunião com cliente",
        "Me lembra de ligar pro dentista na segunda às 9",
        "Marca uma consulta dia 20 de maio às 15:30",
        "Que eventos eu tenho hoje?",
        "O que tem marcado para amanhã?",
        "Quais são meus compromissos da semana?",
        "Manda um email pro João dizendo que a reunião foi cancelada",
        "Envia email para maria@exemplo.com com assunto urgente",
        "Como está o tempo?",
        "Conta uma piada"
    ]
    
    # Cria benchmark
    benchmark = LatencyBenchmark()
    
    # Verifica se sistema está pronto
    if not benchmark.ralu.is_ready():
        print("ERRO: Sistema não está pronto. Verifique se Ollama está rodando.")
        sys.exit(1)
    
    print("Sistema pronto. Iniciando benchmark...")
    print()
    
    # Executa
    benchmark.run_benchmark(test_phrases, iterations=3)
    
    # Relatório
    benchmark.print_report()
    
    # Salva
    benchmark.save_results()
    
    print("\nBenchmark concluído!")


if __name__ == "__main__":
    main()
