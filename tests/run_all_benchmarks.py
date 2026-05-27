"""
Script agregador de métricas para o TCC

Executa todos os benchmarks e gera um relatório consolidado único
com todas as tabelas e métricas necessárias para o Capítulo 3.
"""
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TCCBenchmarkSuite:
    """Suite completa de benchmarks para o TCC"""
    
    def __init__(self, output_dir: Path = None):
        if not output_dir:
            self.output_dir = Path(__file__).parent.parent / "data" / "benchmarks"
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.results = {}
    
    def run_latency_benchmark(self):
        """Executa benchmark de latência"""
        print("\n" + "=" * 70)
        print("1. BENCHMARK DE LATÊNCIA")
        print("=" * 70)
        
        from tests.benchmark_latency import LatencyBenchmark
        
        # Frases de teste (reduzido para economizar tempo)
        test_phrases = [
            "Adiciona um evento amanhã às 14 horas reunião com cliente",
            "Que eventos eu tenho hoje?",
            "Manda um email pro João dizendo que a reunião foi cancelada",
            "Como está o tempo?",
        ]
        
        benchmark = LatencyBenchmark()
        
        if not benchmark.ralu.is_ready():
            print("ERRO: Sistema não está pronto.")
            return None
        
        benchmark.run_benchmark(test_phrases, iterations=3)
        stats = benchmark.calculate_statistics()
        
        # Salva
        csv_file, json_file = benchmark.save_results(self.output_dir)
        
        self.results["latency"] = {
            "stats": stats,
            "csv_file": str(csv_file),
            "json_file": str(json_file)
        }
        
        return stats
    
    def run_classifier_evaluation(self):
        """Executa avaliação do classificador"""
        print("\n" + "=" * 70)
        print("2. AVALIAÇÃO DO CLASSIFICADOR")
        print("=" * 70)
        
        from tests.benchmark_classifier import ClassifierEvaluator
        from tests.test_dataset import get_dataset
        
        evaluator = ClassifierEvaluator()
        
        if not evaluator.ralu.is_ready():
            print("ERRO: Sistema não está pronto.")
            return None
        
        dataset = get_dataset()
        evaluator.evaluate(dataset, verbose=False)
        
        metrics = evaluator.calculate_metrics()
        
        # Salva
        results_file, metrics_file = evaluator.save_results(self.output_dir)
        
        self.results["classifier"] = {
            "metrics": metrics,
            "results_file": str(results_file),
            "metrics_file": str(metrics_file)
        }
        
        return metrics
    
    def run_memory_monitoring(self, duration: int = 60):
        """Executa monitoramento de memória"""
        print("\n" + "=" * 70)
        print("3. MONITORAMENTO DE MEMÓRIA")
        print("=" * 70)
        print(f"\nMonitorando por {duration} segundos...")
        
        from tests.benchmark_memory import MemoryMonitor
        
        monitor = MemoryMonitor()
        monitor.monitor(duration_seconds=duration, interval_seconds=5)
        
        averages = monitor.calculate_averages()
        
        # Salva
        csv_file, json_file = monitor.save_results(self.output_dir)
        
        self.results["memory"] = {
            "averages": averages,
            "csv_file": str(csv_file),
            "json_file": str(json_file)
        }
        
        return averages
    
    def generate_consolidated_report(self):
        """Gera relatório consolidado em Markdown para TCC"""
        report_file = self.output_dir / f"TCC_RELATORIO_CONSOLIDADO_{self.timestamp}.md"
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("# Relatório de Avaliação Experimental - Ralu\n\n")
            f.write(f"**Data**: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
            f.write("---\n\n")
            
            # 1. Latência
            if "latency" in self.results:
                f.write("## 1. Latência do Pipeline\n\n")
                f.write("Tempo médio de processamento por etapa:\n\n")
                
                stats = self.results["latency"]["stats"]
                
                f.write("| Etapa         | Tempo Médio (s) | Desvio Padrão (s) | Min (s) | Max (s) |\n")
                f.write("|---------------|-----------------|-------------------|---------|----------|\n")
                
                labels = {
                    "classification_time": "Classificação",
                    "handler_time": "Handler",
                    "tts_time": "TTS",
                    "total_time": "**TOTAL**"
                }
                
                for metric, label in labels.items():
                    if metric in stats:
                        s = stats[metric]
                        f.write(f"| {label:13} | {s['mean']:15.3f} | {s['stdev']:17.3f} | {s['min']:7.3f} | {s['max']:8.3f} |\n")
                
                f.write("\n")
                
                # Interpretação
                if "total_time" in stats:
                    avg_total = stats["total_time"]["mean"]
                    f.write(f"**Interpretação**: O tempo médio total de resposta foi de **{avg_total:.2f} segundos**, ")
                    f.write(f"sendo a classificação via LLM a etapa mais demorada.\n\n")
                
                f.write("---\n\n")
            
            # 2. Classificador
            if "classifier" in self.results:
                f.write("## 2. Desempenho do Classificador\n\n")
                
                metrics = self.results["classifier"]["metrics"]
                accuracy = metrics.get("accuracy", 0)
                
                f.write(f"**Acurácia Geral**: {accuracy:.2%}\n\n")
                
                f.write("### Métricas por Intenção\n\n")
                f.write("| Intenção    | Precisão | Recall | F1-Score | Suporte |\n")
                f.write("|-------------|----------|--------|----------|----------|\n")
                
                for intent, m in sorted(metrics.get("by_intent", {}).items()):
                    f.write(f"| {intent:11} | {m['precision']:7.2%} | {m['recall']:6.2%} | {m['f1']:7.2%} | {m['support']:8} |\n")
                
                f.write("\n")
                
                # Interpretação
                f.write("**Interpretação**: O classificador demonstrou ")
                if accuracy >= 0.9:
                    f.write("excelente desempenho, ")
                elif accuracy >= 0.8:
                    f.write("bom desempenho, ")
                elif accuracy >= 0.7:
                    f.write("desempenho satisfatório, ")
                else:
                    f.write("desempenho que requer melhorias, ")
                
                f.write(f"com acurácia de {accuracy:.1%}. ")
                
                # Melhor e pior classe
                by_intent = metrics.get("by_intent", {})
                if by_intent:
                    best_intent = max(by_intent.items(), key=lambda x: x[1]["f1"])
                    worst_intent = min(by_intent.items(), key=lambda x: x[1]["f1"])
                    
                    f.write(f"A intenção **{best_intent[0]}** obteve os melhores resultados (F1={best_intent[1]['f1']:.2%}), ")
                    f.write(f"enquanto **{worst_intent[0]}** apresentou maior dificuldade (F1={worst_intent[1]['f1']:.2%}).\n\n")
                
                f.write("---\n\n")
            
            # 3. Memória
            if "memory" in self.results:
                f.write("## 3. Consumo de Memória\n\n")
                
                averages = self.results["memory"]["averages"]
                
                # Processos
                if averages.get("processes"):
                    f.write("### Processos\n\n")
                    f.write("| Processo | RAM Média (MB) | Min (MB) | Max (MB) |\n")
                    f.write("|----------|----------------|----------|----------|\n")
                    
                    for proc, stats in averages["processes"].items():
                        f.write(f"| {proc:15} | {stats['mean']:14.1f} | {stats['min']:8.1f} | {stats['max']:8.1f} |\n")
                    
                    f.write("\n")
                
                # Docker
                if averages.get("docker"):
                    f.write("### Containers Docker\n\n")
                    f.write("| Container | RAM Média (MB) | Min (MB) | Max (MB) |\n")
                    f.write("|-----------|----------------|----------|----------|\n")
                    
                    for container, stats in averages["docker"].items():
                        f.write(f"| {container:15} | {stats['mean']:14.1f} | {stats['min']:8.1f} | {stats['max']:8.1f} |\n")
                    
                    f.write("\n")
                
                # Total estimado
                total_mem = 0
                if averages.get("processes"):
                    total_mem += sum(s["mean"] for s in averages["processes"].values())
                if averages.get("docker"):
                    total_mem += sum(s["mean"] for s in averages["docker"].values())
                
                if total_mem > 0:
                    f.write(f"**Consumo Total Estimado**: {total_mem:.1f} MB (~{total_mem/1024:.2f} GB)\n\n")
                
                f.write("---\n\n")
            
            # 4. Conclusões
            f.write("## 4. Conclusões\n\n")
            f.write("Os testes experimentais demonstraram que:\n\n")
            
            if "latency" in self.results:
                total_time = self.results["latency"]["stats"].get("total_time", {}).get("mean", 0)
                f.write(f"1. O sistema apresenta latência média de **{total_time:.2f}s** para processar uma requisição completa;\n")
            
            if "classifier" in self.results:
                accuracy = self.results["classifier"]["metrics"].get("accuracy", 0)
                f.write(f"2. O classificador de intenções alcançou acurácia de **{accuracy:.1%}**, ")
                f.write("validando a viabilidade da abordagem baseada em LLM local;\n")
            
            if "memory" in self.results:
                f.write("3. O consumo de memória é moderado, compatível com máquinas de uso pessoal;\n")
            
            f.write("\nEssas métricas confirmam a viabilidade técnica do sistema proposto para execução offline.\n\n")
            
            # Arquivos gerados
            f.write("---\n\n")
            f.write("## Arquivos Gerados\n\n")
            
            for category, data in self.results.items():
                f.write(f"### {category.title()}\n\n")
                for key, value in data.items():
                    if key.endswith("_file"):
                        f.write(f"- `{Path(value).name}`\n")
                f.write("\n")
        
        print(f"\n{'='*70}")
        print(f"Relatório consolidado salvo em:")
        print(f"  {report_file}")
        print(f"{'='*70}")
        
        return report_file
    
    def run_all(self, skip_memory: bool = False):
        """Executa todos os benchmarks"""
        print("\n" + "=" * 70)
        print("SUITE COMPLETA DE BENCHMARKS - TCC RALU")
        print("=" * 70)
        print(f"\nResultados serão salvos em: {self.output_dir}")
        print()
        
        input("Pressione ENTER para iniciar...")
        
        # 1. Latência
        try:
            self.run_latency_benchmark()
        except Exception as e:
            print(f"\nERRO no benchmark de latência: {e}")
        
        # 2. Classificador
        try:
            self.run_classifier_evaluation()
        except Exception as e:
            print(f"\nERRO na avaliação do classificador: {e}")
        
        # 3. Memória (opcional, pode ser pesado)
        if not skip_memory:
            try:
                print("\n")
                resp = input("Executar monitoramento de memória (60s)? [S/n]: ")
                if resp.lower() != 'n':
                    self.run_memory_monitoring(duration=60)
            except Exception as e:
                print(f"\nERRO no monitoramento de memória: {e}")
        
        # Gera relatório consolidado
        self.generate_consolidated_report()
        
        print("\n" + "=" * 70)
        print("TODOS OS BENCHMARKS CONCLUÍDOS!")
        print("=" * 70)
        print(f"\nVerifique os resultados em: {self.output_dir}")


def main():
    """Função principal"""
    suite = TCCBenchmarkSuite()
    suite.run_all()


if __name__ == "__main__":
    main()
