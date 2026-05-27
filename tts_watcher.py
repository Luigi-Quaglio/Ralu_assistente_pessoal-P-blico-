"""
Watcher simples que monitora uma pasta por arquivos .txt recém-criados
e reproduz o conteúdo usando `tts_piper.falar_com_piper`.

Uso:
    python tts_watcher.py --dir C:\path\to\watch

O watcher move arquivos processados para um subdiretório `processed`.
"""
import time
import argparse
import os
import shutil
import logging
import sys
from pathlib import Path

# Garantir que o diretório do projeto (pai de Ralu/) esteja no sys.path
# para que possamos importar o módulo `tts_piper.py` que está na raiz do repo.
try:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
except Exception:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("tts_watcher")


def try_speak(text: str) -> bool:
    try:
        import tts_piper
        return tts_piper.falar_com_piper(text)
    except Exception as e:
        logger.exception("Falha ao executar tts_piper: %s", e)
        return False


def process_file(path: str, processed_dir: str):
    logger.info("Processando %s", path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            texto = f.read().strip()
        if not texto:
            logger.info("Arquivo vazio, movendo para processed: %s", path)
            shutil.move(path, os.path.join(processed_dir, os.path.basename(path)))
            return

        ok = try_speak(texto)
        if ok:
            logger.info("Áudio reproduzido para %s", path)
        else:
            logger.warning("TTS falhou para %s", path)

        # mover para processed (sempre)
        dest = os.path.join(processed_dir, os.path.basename(path))
        shutil.move(path, dest)
        logger.info("Movido para %s", dest)
    except Exception:
        logger.exception("Erro ao processar arquivo %s", path)


def main(watch_dir: str, poll_interval: float = 1.0):
    watch_dir = os.path.abspath(watch_dir)
    processed_dir = os.path.join(watch_dir, "processed")
    os.makedirs(processed_dir, exist_ok=True)
    logger.info("Observando pasta: %s", watch_dir)

    seen = set()
    while True:
        try:
            files = [f for f in os.listdir(watch_dir) if f.endswith(".txt")]
            files.sort()
            for fname in files:
                path = os.path.join(watch_dir, fname)
                # ignorar pasta processed
                if os.path.commonpath([processed_dir, path]) == processed_dir:
                    continue
                if path in seen:
                    continue
                # processar
                process_file(path, processed_dir)
                seen.add(path)
        except KeyboardInterrupt:
            logger.info("Encerrando watcher")
            break
        except Exception:
            logger.exception("Erro no loop do watcher")
        time.sleep(poll_interval)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dir", required=True, help="Diretório a observar")
    p.add_argument("--interval", type=float, default=1.0, help="Intervalo de polling (s)")
    args = p.parse_args()
    main(args.dir, args.interval)
