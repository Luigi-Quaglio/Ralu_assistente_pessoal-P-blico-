"""
Repositório de Contatos
"""
from typing import List, Optional

from src.database.connection import db_manager, DatabaseManager
from src.database.models import Contato
from src.utils import normalizar_texto, textos_similares, texto_contem


class ContatoRepository:
    """CRUD para Contatos"""
    
    def __init__(self, db: DatabaseManager = None):
        self.db = db or db_manager
    
    def criar(self, contato: Contato) -> Contato:
        """Cria um novo contato"""
        with self.db.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO contatos (nome, email, telefone) VALUES (?, ?, ?)",
                (contato.nome, contato.email, contato.telefone)
            )
        return contato
    
    def buscar_por_nome(self, nome: str) -> Optional[Contato]:
        """
        Busca contato pelo nome exato.
        Ignora acentos e maiúsculas/minúsculas.
        
        Exemplo: "João" encontra "joao", "JOAO", "João"
        """
        todos = self.listar_todos()
        for contato in todos:
            if textos_similares(contato.nome, nome):
                return contato
        return None
    
    def listar_todos(self) -> List[Contato]:
        """Lista todos os contatos"""
        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT nome, email, telefone FROM contatos ORDER BY nome")
            return [Contato.from_row(row) for row in cursor.fetchall()]
    
    def buscar(self, termo: str) -> List[Contato]:
        """
        Busca contatos por nome, email ou telefone.
        Ignora acentos e maiúsculas/minúsculas.
        
        Exemplo: "joao" encontra "João Guilherme", "João Vitor"
        """
        todos = self.listar_todos()
        resultados = []
        
        for contato in todos:
            # Busca no nome (ignorando acentos)
            if texto_contem(contato.nome, termo):
                resultados.append(contato)
            # Busca no email
            elif contato.email and texto_contem(contato.email, termo):
                resultados.append(contato)
            # Busca no telefone
            elif contato.telefone and termo in contato.telefone:
                resultados.append(contato)
        
        return resultados
    
    def atualizar(self, contato: Contato) -> bool:
        """
        Atualiza um contato existente.
        Busca ignorando acentos e case.
        """
        # Busca o contato real no banco para pegar o nome exato
        contato_existente = self.buscar_por_nome(contato.nome)
        if not contato_existente:
            return False
        
        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                UPDATE contatos 
                SET email = ?, telefone = ?
                WHERE nome = ?
                """,
                (contato.email, contato.telefone, contato_existente.nome)
            )
            return cursor.rowcount > 0
    
    def deletar(self, nome: str) -> bool:
        """
        Remove um contato pelo nome.
        Busca ignorando acentos e case.
        """
        # Busca o contato real no banco para pegar o nome exato
        contato_existente = self.buscar_por_nome(nome)
        if not contato_existente:
            return False
        
        with self.db.get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM contatos WHERE nome = ?",
                (contato_existente.nome,)
            )
            return cursor.rowcount > 0
    
    def existe(self, nome: str) -> bool:
        """Verifica se um contato existe (ignora acentos e case)"""
        return self.buscar_por_nome(nome) is not None
