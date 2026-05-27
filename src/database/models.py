"""
Modelos do banco de dados SQLite
"""
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from pathlib import Path


# Caminho padrão do banco de dados
DB_PATH = Path(__file__).parent.parent.parent / "data" / "ralu.db"


@dataclass
class Contato:
    """Modelo de Contato"""
    nome: str  # Primary Key
    email: Optional[str] = None
    telefone: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "nome": self.nome,
            "email": self.email,
            "telefone": self.telefone
        }
    
    @classmethod
    def from_row(cls, row: tuple) -> "Contato":
        return cls(nome=row[0], email=row[1], telefone=row[2])


@dataclass
class Evento:
    """Modelo de Evento"""
    id: Optional[int] = None  # Auto-increment
    nome: str = ""
    data: Optional[datetime] = None  # Data/hora de início
    data_fim: Optional[datetime] = None  # Data/hora de fim (para eventos com duração)
    descricao: Optional[str] = None
    participante: Optional[str] = None  # Nome do contato
    lembrete: Optional[datetime] = None
    local: Optional[str] = None
    cor: Optional[str] = None  # Cor do evento (hex: #3498db)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "data": self.data.isoformat() if self.data else None,
            "data_fim": self.data_fim.isoformat() if self.data_fim else None,
            "descricao": self.descricao,
            "participante": self.participante,
            "lembrete": self.lembrete.isoformat() if self.lembrete else None,
            "local": self.local,
            "cor": self.cor
        }
    
    @classmethod
    def from_row(cls, row: tuple) -> "Evento":
        return cls(
            id=row[0],
            nome=row[1],
            data=datetime.fromisoformat(row[2]) if row[2] else None,
            data_fim=datetime.fromisoformat(row[3]) if row[3] else None,
            descricao=row[4],
            participante=row[5],
            lembrete=datetime.fromisoformat(row[6]) if row[6] else None,
            local=row[7],
            cor=row[8] if len(row) > 8 else None
        )
