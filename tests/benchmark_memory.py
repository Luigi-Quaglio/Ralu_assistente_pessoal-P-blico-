"""
Script de medição de consumo de memória RAM

Monitora consumo de RAM de cada componente do sistema:
- Ollama
- Python (Ralu)
- Whisper (se aplicável)
- Docker containers (se aplicável)

Gera relatório para TCC.
"""
import psutil
import subprocess
import time
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
import csv

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))


class MemoryMonitor:
    """Monitora consumo de memória do sistema"""
    
    def __init__(self):
        self.samples: List[Dict] = []
    
    def get_process_memory(self, process_name: str) -> Optional[float]:
        """
        Obtém memória usada por um processo (em MB)
        
        Args:
            process_name: Nome do processo (ex: "ollama", "python")
        
        Returns:
            Memória em MB ou None se processo não encontrado
        """
        total_memory = 0
        found = False
        
        for proc in psutil.process_iter(['name', 'memory_info']):
            try:
                if process_name.lower() in proc.info['name'].lower():
                    memory_mb = proc.info['memory_info'].rss / (1024 * 1024)
                    total_memory += memory_mb
                    found = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return total_memory if found else None
    
    def get_docker_stats(self) -> Dict[str, float]:
        """
        Obtém estatísticas de memória dos containers Docker
        
        Returns:
            Dict com nome do container e memória em MB
        """
        stats = {}
        
        try:
            # Tenta obter stats do Docker
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "{{.Name}}\t{{.MemUsage}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if '\t' in line:
                        name, mem_usage = line.split('\t')
                        # Parse formato "123.4MiB / 1.234GiB"
                        mem_str = mem_usage.split('/')[0].strip()
                        
                        # Converter para MB
                        if 'GiB' in mem_str or 'GB' in mem_str:
                            mem_mb = float(mem_str.replace('GiB', '').replace('GB', '').strip()) * 1024
                        elif 'MiB' in mem_str or 'MB' in mem_str:
                            mem_mb = float(mem_str.replace('MiB', '').replace('MB', '').strip())
                        else:
                            mem_mb = 0
                        
                        stats[name] = mem_mb
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return stats
    
    def get_system_memory(self) -> Dict[str, float]:
        """Obtém memória total do sistema"""
        mem = psutil.virtual_memory()
        return {
            "total_mb": mem.total / (1024 * 1024),
            "available_mb": mem.available / (1024 * 1024),
            "used_mb": mem.used / (1024 * 1024),
            "percent": mem.percent
        }
    
    def take_snapshot(self) -> Dict:
        """Captura um snapshot da memória atual"""
        snapshot = {
            "timestamp": time.time(),
            "time_str": time.strftime("%Y-%m-%d %H:%M:%S"),
            "processes": {},
            "docker": {},
            "system": self.get_system_memory()
        }
        
        # Processos de interesse
        processes_to_monitor = ["ollama", "python", "whisper"]
        
        for proc_name in processes_to_monitor:
            mem = self.get_process_memory(proc_name)
            if mem is not None:
                snapshot["processes"][proc_name] = mem
        
        # Docker
        docker_stats = self.get_docker_stats()
        snapshot["docker"] = docker_stats
        
        return snapshot
    
    def monitor(self, duration_seconds: int = 60, interval_seconds: int = 5):
        """
        Monitora memória por um período
        
        Args:
            duration_seconds: Duração total do monitoramento
            interval_seconds: Intervalo entre amostras
        """
        print(f"Monitorando memória por {duration_seconds}s (intervalo: {interval_seconds}s)...")
        print("=" * 70)
        
        start_time = time.time()
        sample_count = 0
        
        while time.time() - start_time < duration_seconds:
            sample_count += 1
            snapshot = self.take_snapshot()
            self.samples.append(snapshot)
            
            # Exibe snapshot
            print(f"\n[Amostra {sample_count}] {snapshot['time_str']}")
            print(f"Sistema: {snapshot['system']['used_mb']:.1f} MB / {snapshot['system']['total_mb']:.1f} MB ({snapshot['system']['percent']:.1f}%)")
            
            if snapshot['processes']:
                print("Processos:")
                for name, mem in snapshot['processes'].items():
                    print(f"  - {name}: {mem:.1f} MB")
            
            if snapshot['docker']:
                print("Docker:")
                for name, mem in snapshot['docker'].items():
                    print(f"  - {name}: {mem:.1f} MB")
            
            # Aguarda intervalo
            time.sleep(interval_seconds)
        
        print("\n" + "=" * 70)
        print(f"Monitoramento concluído. {len(self.samples)} amostras coletadas.")
    
    def calculate_averages(self) -> Dict:
        """Calcula médias de uso de memória"""
        if not self.samples:
            return {}
        
        averages = {
            "processes": {},
            "docker": {},
            "system": {}
        }
        
        # Processos
        all_process_names = set()
        for sample in self.samples:
            all_process_names.update(sample['processes'].keys())
        
        for proc_name in all_process_names:
            values = [s['processes'].get(proc_name, 0) for s in self.samples if proc_name in s['processes']]
            if values:
                averages['processes'][proc_name] = {
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values)
                }
        
        # Docker
        all_container_names = set()
        for sample in self.samples:
            all_container_names.update(sample['docker'].keys())
        
        for container in all_container_names:
            values = [s['docker'].get(container, 0) for s in self.samples if container in s['docker']]
            if values:
                averages['docker'][container] = {
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values)
                }
        
        # Sistema
        system_values = [s['system']['used_mb'] for s in self.samples]
        if system_values:
            averages['system'] = {
                "mean": sum(system_values) / len(system_values),
                "min": min(system_values),
                "max": max(system_values)
            }
        
        return averages
    
    def save_results(self, output_dir: Path = None):
        """Salva resultados em CSV e JSON"""
        if not output_dir:
            output_dir = Path(__file__).parent.parent / "data" / "benchmarks"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # CSV com amostras
        csv_file = output_dir / f"memory_samples_{timestamp}.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Component", "Memory_MB"])
            
            for sample in self.samples:
                ts = sample['time_str']
                for proc_name, mem in sample['processes'].items():
                    writer.writerow([ts, f"Process_{proc_name}", f"{mem:.2f}"])
                for container, mem in sample['docker'].items():
                    writer.writerow([ts, f"Docker_{container}", f"{mem:.2f}"])
                writer.writerow([ts, "System_Total", f"{sample['system']['used_mb']:.2f}"])
        
        print(f"\nAmostras salvas em: {csv_file}")
        
        # JSON com médias
        averages = self.calculate_averages()
        json_file = output_dir / f"memory_averages_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(averages, f, indent=2, ensure_ascii=False)
        
        print(f"Médias salvas em: {json_file}")
        
        return csv_file, json_file
    
    def print_report(self):
        """Imprime relatório de memória"""
        averages = self.calculate_averages()
        
        print("\n" + "=" * 70)
        print("RELATÓRIO DE CONSUMO DE MEMÓRIA")
        print("=" * 70)
        
        print(f"\nAmostras coletadas: {len(self.samples)}")
        
        # Processos
        if averages.get('processes'):
            print("\n┌─────────────────────────┬──────────┬──────────┬──────────┐")
            print("│ Processo                │   Média  │  Mínimo  │  Máximo  │")
            print("├─────────────────────────┼──────────┼──────────┼──────────┤")
            
            for proc_name, stats in averages['processes'].items():
                print(f"│ {proc_name:23} │ {stats['mean']:7.1f}  │ {stats['min']:7.1f}  │ {stats['max']:7.1f}  │")
            
            print("└─────────────────────────┴──────────┴──────────┴──────────┘")
        
        # Docker
        if averages.get('docker'):
            print("\n┌─────────────────────────┬──────────┬──────────┬──────────┐")
            print("│ Container               │   Média  │  Mínimo  │  Máximo  │")
            print("├─────────────────────────┼──────────┼──────────┼──────────┤")
            
            for container, stats in averages['docker'].items():
                print(f"│ {container:23} │ {stats['mean']:7.1f}  │ {stats['min']:7.1f}  │ {stats['max']:7.1f}  │")
            
            print("└─────────────────────────┴──────────┴──────────┴──────────┘")
        
        print("\n(Todos os valores em MB)")
        
        # Tabela para TCC
        print("\n" + "=" * 70)
        print("TABELA PARA TCC (Markdown)")
        print("=" * 70)
        print("\n| Serviço | RAM (MB) |")
        print("| ------- | -------- |")
        
        for proc_name, stats in averages.get('processes', {}).items():
            print(f"| {proc_name:15} | {stats['mean']:7.1f}  |")
        
        for container, stats in averages.get('docker', {}).items():
            print(f"| {container:15} | {stats['mean']:7.1f}  |")


def main():
    """Função principal"""
    print("MONITOR DE MEMÓRIA - Ralu TCC")
    print("=" * 70)
    print("\nEste script irá monitorar o consumo de memória do sistema.")
    print("Certifique-se de que o sistema Ralu está rodando.\n")
    
    input("Pressione ENTER para iniciar o monitoramento...")
    
    monitor = MemoryMonitor()
    
    # Monitora por 2 minutos, amostrando a cada 5 segundos
    monitor.monitor(duration_seconds=120, interval_seconds=5)
    
    # Relatório
    monitor.print_report()
    
    # Salva
    monitor.save_results()
    
    print("\nMonitoramento concluído!")


if __name__ == "__main__":
    main()
