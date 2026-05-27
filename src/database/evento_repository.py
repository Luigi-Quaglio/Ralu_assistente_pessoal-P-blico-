"""
Repositório de Eventos
"""
from datetime import datetime, timedelta
from typing import List, Optional

from src.database.connection import db_manager, DatabaseManager
from src.database.models import Evento


class EventoRepository:
    """CRUD para Eventos"""
    
    def __init__(self, db: DatabaseManager = None):
        self.db = db or db_manager
    
    def criar(self, evento: Evento) -> Evento:
        """Cria um novo evento"""
        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO eventos (nome, data, data_fim, descricao, participante, lembrete, local, cor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evento.nome,
                    evento.data.isoformat() if evento.data else None,
                    evento.data_fim.isoformat() if evento.data_fim else None,
                    evento.descricao,
                    evento.participante,
                    evento.lembrete.isoformat() if evento.lembrete else None,
                    evento.local,
                    evento.cor
                )
            )
            evento.id = cursor.lastrowid
        return evento
    
    def buscar_por_id(self, id: int) -> Optional[Evento]:
        """Busca evento pelo ID"""
        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, nome, data, data_fim, descricao, participante, lembrete, local, cor 
                FROM eventos WHERE id = ?
                """,
                (id,)
            )
            row = cursor.fetchone()
            return Evento.from_row(row) if row else None
    
    def listar_todos(self) -> List[Evento]:
        """Lista todos os eventos ordenados por data"""
        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, nome, data, data_fim, descricao, participante, lembrete, local, cor 
                FROM eventos ORDER BY data
                """
            )
            return [Evento.from_row(row) for row in cursor.fetchall()]
    
    def buscar_por_data(self, data: datetime) -> List[Evento]:
        """Busca eventos de um dia específico"""
        data_inicio = data.replace(hour=0, minute=0, second=0, microsecond=0)
        data_fim = data_inicio + timedelta(days=1)
        
        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, nome, data, data_fim, descricao, participante, lembrete, local, cor 
                FROM eventos 
                WHERE data >= ? AND data < ?
                ORDER BY data
                """,
                (data_inicio.isoformat(), data_fim.isoformat())
            )
            return [Evento.from_row(row) for row in cursor.fetchall()]
    
    def buscar_por_periodo(self, inicio: datetime, fim: datetime) -> List[Evento]:
        """Busca eventos em um período"""
        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, nome, data, data_fim, descricao, participante, lembrete, local, cor 
                FROM eventos 
                WHERE data >= ? AND data <= ?
                ORDER BY data
                """,
                (inicio.isoformat(), fim.isoformat())
            )
            return [Evento.from_row(row) for row in cursor.fetchall()]
    
    def buscar_por_participante(self, participante: str) -> List[Evento]:
        """Busca eventos de um participante"""
        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, nome, data, data_fim, descricao, participante, lembrete, local, cor 
                FROM eventos 
                WHERE LOWER(participante) = LOWER(?)
                ORDER BY data
                """,
                (participante,)
            )
            return [Evento.from_row(row) for row in cursor.fetchall()]
    
    def buscar_proximos(self, dias: int = 7) -> List[Evento]:
        """Busca eventos dos próximos N dias"""
        agora = datetime.now()
        fim = agora + timedelta(days=dias)
        return self.buscar_por_periodo(agora, fim)
    
    def buscar_hoje(self) -> List[Evento]:
        """Busca eventos de hoje"""
        return self.buscar_por_data(datetime.now())
    
    def buscar(self, termo: str) -> List[Evento]:
        """Busca eventos por nome, descrição ou local"""
        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, nome, data, data_fim, descricao, participante, lembrete, local, cor 
                FROM eventos 
                WHERE LOWER(nome) LIKE LOWER(?)
                   OR LOWER(descricao) LIKE LOWER(?)
                   OR LOWER(local) LIKE LOWER(?)
                ORDER BY data
                """,
                (f"%{termo}%", f"%{termo}%", f"%{termo}%")
            )
            return [Evento.from_row(row) for row in cursor.fetchall()]
    
    def atualizar(self, evento: Evento) -> bool:
        """Atualiza um evento existente"""
        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE eventos 
                SET nome = ?, data = ?, data_fim = ?, descricao = ?, 
                    participante = ?, lembrete = ?, local = ?, cor = ?
                WHERE id = ?
                """,
                (
                    evento.nome,
                    evento.data.isoformat() if evento.data else None,
                    evento.data_fim.isoformat() if evento.data_fim else None,
                    evento.descricao,
                    evento.participante,
                    evento.lembrete.isoformat() if evento.lembrete else None,
                    evento.local,
                    evento.cor,
                    evento.id
                )
            )
            return cursor.rowcount > 0
    
    def deletar(self, id: int) -> bool:
        """Remove um evento pelo ID"""
        with self.db.get_cursor() as cursor:
            cursor.execute("DELETE FROM eventos WHERE id = ?", (id,))
            return cursor.rowcount > 0
    
    def buscar_lembretes_pendentes(self) -> List[Evento]:
        """Busca eventos com lembretes que devem ser disparados"""
        agora = datetime.now().isoformat()
        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT id, nome, data, data_fim, descricao, participante, lembrete, local, cor 
                FROM eventos 
                WHERE lembrete IS NOT NULL AND lembrete <= ? AND data > ?
                ORDER BY lembrete
                """,
                (agora, agora)
            )
            return [Evento.from_row(row) for row in cursor.fetchall()]
