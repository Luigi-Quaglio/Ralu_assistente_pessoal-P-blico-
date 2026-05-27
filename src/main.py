"""
Ponto de entrada principal do Ralu
"""
import json
import sys
import argparse

from src.ralu import Ralu


def main():
    parser = argparse.ArgumentParser(description="Ralu - Classificador de Intenções")
    parser.add_argument("text", nargs="?", help="Texto para classificar")
    parser.add_argument("--interactive", "-i", action="store_true", help="Modo interativo")
    parser.add_argument("--url", default=None, help="URL do Ollama")
    parser.add_argument("--model", default=None, help="Nome do modelo")
    
    args = parser.parse_args()
    
    ralu = Ralu(ollama_url=args.url, model=args.model)
    
    # Verifica se está pronto
    if not ralu.is_ready():
        print("Erro: Servidor Ollama não está disponível ou modelo não encontrado")
        sys.exit(1)
    
    if args.interactive:
        interactive_mode(ralu)
    elif args.text:
        result = ralu.process(args.text)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        parser.print_help()


def interactive_mode(ralu: Ralu):
    """Modo interativo de conversação"""
    print("=" * 60)
    print("Ralu - Classificador de Intenções")
    print("Digite 'sair' para encerrar")
    print("=" * 60)
    
    while True:
        try:
            text = input("\nVocê: ").strip()
            
            if text.lower() in ["sair", "exit", "quit"]:
                print("Até logo!")
                break
            
            if not text:
                continue
            
            result = ralu.process(text)
            print(f"\nResultado: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
        except KeyboardInterrupt:
            print("\nAté logo!")
            break
        except Exception as e:
            print(f"Erro: {e}")


if __name__ == "__main__":
    main()
