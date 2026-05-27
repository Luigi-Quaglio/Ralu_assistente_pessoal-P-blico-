"""
Gerenciador de conexão com o banco de dados SQLite
"""
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from src.database.models import DB_PATH


class DatabaseManager:
    """Gerencia conexões com o banco SQLite"""
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or DB_PATH
        self._ensure_db_dir()
    
    def _ensure_db_dir(self):
        """Cria o diretório do banco se não existir"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager para conexão com o banco"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    @contextmanager
    def get_cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """Context manager para cursor"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            yield cursor
    
    def init_db(self):
        """Inicializa o banco de dados com as tabelas"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabela Contatos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contatos (
                    nome TEXT PRIMARY KEY,
                    email TEXT,
                    telefone TEXT
                )
            """)
            
            # Tabela Eventos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS eventos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    data TEXT,
                    data_fim TEXT,
                    descricao TEXT,
                    participante TEXT,
                    lembrete TEXT,
                    local TEXT,
                    FOREIGN KEY (participante) REFERENCES contatos(nome)
                )
            """)
            
            # Migração: adiciona coluna data_fim se não existir
            try:
                cursor.execute("ALTER TABLE eventos ADD COLUMN data_fim TEXT")
            except sqlite3.OperationalError:
                pass  # Coluna já existe
            
            # Migração: adiciona coluna cor se não existir
            try:
                cursor.execute("ALTER TABLE eventos ADD COLUMN cor TEXT")
            except sqlite3.OperationalError:
                pass  # Coluna já existe
            
            # Índices para buscas
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_eventos_data 
                ON eventos(data)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_eventos_participante 
                ON eventos(participante)
            """)
            
            conn.commit()
            print(f"Banco de dados inicializado em: {self.db_path}")


# Instância global
db_manager = DatabaseManager()
