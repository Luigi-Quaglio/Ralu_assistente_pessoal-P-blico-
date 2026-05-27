"""
Database - Módulo de persistência SQLite
"""
from src.database.models import Contato, Evento, DB_PATH
from src.database.connection import DatabaseManager, db_manager
from src.database.contato_repository import ContatoRepository
from src.database.evento_repository import EventoRepository


def init_database():
    """Inicializa o banco de dados"""
    db_manager.init_db()


__all__ = [
    "Contato",
    "Evento",
    "DB_PATH",
    "DatabaseManager",
    "db_manager",
    "ContatoRepository",
    "EventoRepository",
    "init_database",
]
