"""
Handler para envio de emails
"""
import logging
from typing import Any, Dict, List, Optional

from src.models import IntentResult, IntentType
from src.handlers.base import BaseHandler
from src.database import ContatoRepository, Contato, init_database

logger = logging.getLogger(__name__)


class EmailHandler(BaseHandler):
    """Handler para intenção de envio de email"""
    
    intent_type = IntentType.SEND_EMAIL
    
    def __init__(self):
        init_database()
        self.contatos_repo = ContatoRepository()
    
    def validate(self, intent_result: IntentResult) -> tuple[bool, Optional[str]]:
        """Valida se tem destinatário"""
        entities = intent_result.entities
        
        if not entities.get("recipient"):
            return False, "Destinatário não especificado"
        
        return True, None
    
    def execute(self, intent_result: IntentResult) -> Dict[str, Any]:
        """
        Executa o envio de email.
        Busca o email do contato na base de dados.
        Se houver múltiplos contatos, pede para escolher.
        """
        entities = intent_result.entities
        recipient_nome = entities.get("recipient")
        subject = entities.get("subject")
        
        # Primeiro tenta busca exata
        contato = self.contatos_repo.buscar_por_nome(recipient_nome)
        
        if contato and contato.email:
            return self._enviar_email(contato, subject, intent_result)
        
        # Busca parcial
        contatos = self.contatos_repo.buscar(recipient_nome)
        contatos_com_email = [c for c in contatos if c.email]
        
        if len(contatos_com_email) == 0:
            print(f"\n⚠️  Contato '{recipient_nome}' não encontrado ou sem email cadastrado\n")
            logger.warning(f"Contato não encontrado: {recipient_nome}")
            
            return {
                "success": False,
                "action": "send_email",
                "intent": intent_result.intent.value,
                "error": "contato_nao_encontrado",
                "message": f"Contato '{recipient_nome}' não encontrado. Cadastre primeiro em Contatos."
            }
        
        if len(contatos_com_email) == 1:
            return self._enviar_email(contatos_com_email[0], subject, intent_result)
        
        # Múltiplos contatos encontrados - pede para escolher
        opcoes = [{"nome": c.nome, "email": c.email} for c in contatos_com_email]
        nomes = [c.nome for c in contatos_com_email]
        
        logger.info(f"Múltiplos contatos encontrados para '{recipient_nome}': {nomes}")
        
        return {
            "success": False,
            "action": "send_email",
            "intent": intent_result.intent.value,
            "needs_followup": True,
            "followup_type": "select_contact",
            "pending_email": {
                "subject": subject,
                "raw_text": intent_result.raw_text
            },
            "options": opcoes,
            "message": f"Qual {recipient_nome}? " + ", ".join(nomes) + "?"
        }
    
    def execute_with_contact(self, contato_nome: str, pending_email: Dict) -> Dict[str, Any]:
        """
        Completa o envio de email com contato selecionado.
        """
        contato = self.contatos_repo.buscar_por_nome(contato_nome)
        
        if not contato:
            # Tenta busca parcial
            contatos = self.contatos_repo.buscar(contato_nome)
            if contatos:
                contato = contatos[0]
        
        if not contato or not contato.email:
            return {
                "success": False,
                "action": "send_email",
                "intent": IntentType.SEND_EMAIL.value,
                "error": "contato_nao_encontrado",
                "message": f"Contato '{contato_nome}' não encontrado."
            }
        
        subject = pending_email.get("subject")
        return self._enviar_email(contato, subject)
    
    def _enviar_email(self, contato: Contato, subject: str, intent_result: IntentResult = None) -> Dict[str, Any]:
        """Executa o envio de email para um contato específico"""
        email = contato.email
        print(f"\n{'='*50}")
        print(f"📧 EMAIL PARA: {email}")
        print(f"   Destinatário: {contato.nome}")
        if subject:
            print(f"   Assunto: {subject}")
        print(f"{'='*50}\n")
        logger.info(f"Email preparado para {contato.nome} <{email}>")
        
        return {
            "success": True,
            "action": "send_email",
            "intent": IntentType.SEND_EMAIL.value,
            "data": {
                "recipient": contato.nome,
                "email": email,
                "subject": subject
            },
            "message": f"Email para {contato.nome} ({email})"
        }
