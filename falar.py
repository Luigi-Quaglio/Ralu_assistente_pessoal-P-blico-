"""
Modo interativo: digite texto e a Ralu fala.
Sair: ENTER vazio ou Ctrl+C
"""
from tts_piper import falar_com_piper

print("=== Ralu TTS — Microsoft Maria (PT-BR) ===")
print("ENTER vazio para sair\n")

while True:
    try:
        texto = input(">>> ")
    except (KeyboardInterrupt, EOFError):
        print("\nAté logo!")
        break

    if not texto.strip():
        print("Até logo!")
        break

    falar_com_piper(texto)
