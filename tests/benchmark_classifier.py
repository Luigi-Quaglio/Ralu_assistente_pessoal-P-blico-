"""
Script de avaliação do classificador de intenções

Testa o classificador contra um dataset anotado manualmente.
Calcula métricas: acurácia, precisão, recall, F1-score.
Gera matriz de confusão e relatório para o TCC.
"""
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ralu import Ralu
from tests.test_dataset import get_dataset, get_intent_counts


class ClassifierEvaluator:
    """Avalia o desempenho do classificador de intenções"""
    
    def __init__(self):
        self.ralu = Ralu()
        self.results: List[Dict] = []
        self.confusion_matrix = defaultdict(lambda: defaultdict(int))
    
    def evaluate(self, dataset: List[Dict[str, str]], verbose: bool = True):
        """
        Avalia o classificador no dataset
        
        Args:
            dataset: Lista de dicts com 'text' e 'expected_intent'
            verbose: Se True, imprime progresso
        """
        if verbose:
            print(f"Avaliando classificador com {len(dataset)} exemplos...")
            print("=" * 70)
        
        for i, item in enumerate(dataset, 1):
            text = item["text"]
            expected = item["expected_intent"]
            
            if verbose:
                print(f"[{i}/{len(dataset)}] {text[:50]}...")
            
            try:
                # Classifica
                start = time.time()
                intent_result = self.ralu.classify(text)
                elapsed = time.time() - start
                
                predicted = intent_result.intent.value
                confidence = intent_result.confidence
                
                # Verifica se acertou
                correct = (predicted == expected)
                
                # Armazena resultado
                result = {
                    "text": text,
                    "expected": expected,
                    "predicted": predicted,
                    "confidence": confidence,
                    "correct": correct,
                    "time": elapsed
                }
                self.results.append(result)
                
                # Atualiza matriz de confusão
                self.confusion_matrix[expected][predicted] += 1
                
                if verbose:
                    status = "✓" if correct else "✗"
                    print(f"  {status} Esperado: {expected}, Predito: {predicted} (conf: {confidence:.2f})")
            
            except Exception as e:
                if verbose:
                    print(f"  ✗ ERRO: {e}")
                
                # Marca como erro
                result = {
                    "text": text,
                    "expected": expected,
                    "predicted": "ERROR",
                    "confidence": 0.0,
                    "correct": False,
                    "time": 0.0,
                    "error": str(e)
                }
                self.results.append(result)
            
            # Pequena pausa entre requests
            time.sleep(0.3)
        
        if verbose:
            print("\n" + "=" * 70)
            print("Avaliação concluída!")
    
    def calculate_metrics(self) -> Dict:
        """
        Calcula métricas de avaliação
        
        Returns:
            Dict com acurácia, precisão, recall, F1 por classe
        """
        if not self.results:
            return {}
        
        # Acurácia geral
        correct = sum(1 for r in self.results if r["correct"])
        total = len(self.results)
        accuracy = correct / total if total > 0 else 0
        
        # Métricas por classe
        intents = set()
        for r in self.results:
            intents.add(r["expected"])
            intents.add(r["predicted"])
        
        metrics_by_intent = {}
        
        for intent in intents:
            if intent == "ERROR":
                continue
            
            # True Positives: predito=intent e esperado=intent
            tp = sum(1 for r in self.results if r["predicted"] == intent and r["expected"] == intent)
            
            # False Positives: predito=intent mas esperado!=intent
            fp = sum(1 for r in self.results if r["predicted"] == intent and r["expected"] != intent)
            
            # False Negatives: predito!=intent mas esperado=intent
            fn = sum(1 for r in self.results if r["predicted"] != intent and r["expected"] == intent)
            
            # Precisão: dos que predisse como intent, quantos eram realmente?
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            
            # Recall: dos que eram intent, quantos conseguiu identificar?
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            
            # F1-score: média harmônica
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            metrics_by_intent[intent] = {
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "support": tp + fn  # número de exemplos reais dessa classe
            }
        
        return {
            "accuracy": accuracy,
            "total_correct": correct,
            "total_samples": total,
            "by_intent": metrics_by_intent
        }
    
    def print_confusion_matrix(self):
        """Imprime matriz de confusão"""
        print("\n" + "=" * 70)
        print("MATRIZ DE CONFUSÃO")
        print("=" * 70)
        print("\n(Linhas = Esperado, Colunas = Predito)\n")
        
        # Obtém todas as classes
        all_intents = sorted(set(list(self.confusion_matrix.keys()) + 
                                 [k for row in self.confusion_matrix.values() for k in row.keys()]))
        
        # Cabeçalho
        header = "Esperado \\ Predito".ljust(20)
        for intent in all_intents:
            header += f"{intent[:10]:>12}"
        print(header)
        print("-" * len(header))
        
        # Linhas
        for expected in all_intents:
            row = expected.ljust(20)
            for predicted in all_intents:
                count = self.confusion_matrix[expected][predicted]
                row += f"{count:>12}"
            print(row)
    
    def print_report(self):
        """Imprime relatório completo"""
        metrics = self.calculate_metrics()
        
        print("\n" + "=" * 70)
        print("RELATÓRIO DE AVALIAÇÃO DO CLASSIFICADOR")
        print("=" * 70)
        
        print(f"\nAcurácia Geral: {metrics['accuracy']:.2%} ({metrics['total_correct']}/{metrics['total_samples']})")
        
        print("\n┌─────────────────┬───────────┬──────────┬──────────┬─────────┐")
        print("│ Intenção        │ Precisão  │  Recall  │ F1-Score │ Suporte │")
        print("├─────────────────┼───────────┼──────────┼──────────┼─────────┤")
        
        for intent, m in sorted(metrics["by_intent"].items()):
            print(f"│ {intent:15} │   {m['precision']:5.2%}   │  {m['recall']:5.2%}  │  {m['f1']:5.2%}  │  {m['support']:4}   │")
        
        print("└─────────────────┴───────────┴──────────┴──────────┴─────────┘")
        
        # Matriz de confusão
        self.print_confusion_matrix()
        
        # Tabela para TCC
        print("\n" + "=" * 70)
        print("TABELA PARA TCC (Markdown)")
        print("=" * 70)
        print("\n| Intenção    | Precisão | Recall | F1-Score | Acertos/Total |")
        print("| ----------- | -------- | ------ | -------- | ------------- |")
        
        for intent, m in sorted(metrics["by_intent"].items()):
            # Calcula acertos
            correct = sum(1 for r in self.results if r["expected"] == intent and r["correct"])
            total = m["support"]
            print(f"| {intent:11} | {m['precision']:6.2%}   | {m['recall']:5.2%} | {m['f1']:6.2%}   | {correct}/{total:2}          |")
        
        print(f"\n**Acurácia Geral**: {metrics['accuracy']:.2%}")
    
    def save_results(self, output_dir: Path = None):
        """Salva resultados em JSON"""
        if not output_dir:
            output_dir = Path(__file__).parent.parent / "data" / "benchmarks"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Resultados detalhados
        results_file = output_dir / f"classifier_results_{timestamp}.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\nResultados salvos em: {results_file}")
        
        # Métricas
        metrics = self.calculate_metrics()
        metrics_file = output_dir / f"classifier_metrics_{timestamp}.json"
        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        print(f"Métricas salvas em: {metrics_file}")
        
        return results_file, metrics_file


def main():
    """Função principal"""
    print("AVALIAÇÃO DO CLASSIFICADOR - Ralu TCC")
    print("=" * 70)
    
    # Carrega dataset
    dataset = get_dataset()
    
    print(f"\nDataset: {len(dataset)} exemplos")
    print("\nDistribuição:")
    for intent, count in sorted(get_intent_counts().items()):
        print(f"  - {intent}: {count}")
    
    print()
    input("Pressione ENTER para iniciar avaliação...")
    print()
    
    # Cria avaliador
    evaluator = ClassifierEvaluator()
    
    # Verifica se sistema está pronto
    if not evaluator.ralu.is_ready():
        print("ERRO: Sistema não está pronto. Verifique se Ollama está rodando.")
        sys.exit(1)
    
    # Avalia
    evaluator.evaluate(dataset, verbose=True)
    
    # Relatório
    evaluator.print_report()
    
    # Salva
    evaluator.save_results()
    
    print("\nAvaliação concluída!")


if __name__ == "__main__":
    main()
