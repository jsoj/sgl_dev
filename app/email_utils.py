import logging
import socket
from smtplib import SMTPException
from django.core.mail import EmailMessage, send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

def enviar_email_com_retry(assunto, mensagem, destinatarios, anexo=None, anexo_content=None, anexo_mimetype=None):
    """
    Função para enviar emails com tratamento de erro detalhado e retry
    
    Args:
        assunto: Assunto do email
        mensagem: Corpo do email
        destinatarios: Lista de destinatários 
        anexo: Opcional - nome do arquivo anexo
        anexo_content: Opcional - conteúdo do anexo (bytes)
        anexo_mimetype: Opcional - tipo MIME do anexo
        
    Returns:
        bool: True se o email foi enviado com sucesso, False caso contrário
    """
    # Configurações de debug
    if settings.EMAIL_DEBUG:
        logger.info(f"Tentando enviar email: '{assunto}' para {destinatarios}")
        logger.info(f"Usando servidor: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        logger.info(f"Usando usuário: {settings.EMAIL_HOST_USER}")
        logger.info(f"TLS habilitado: {settings.EMAIL_USE_TLS}")
        logger.info(f"SSL habilitado: {settings.EMAIL_USE_SSL}")
    
    # Prepara o email
    email = EmailMessage(
        subject=assunto,
        body=mensagem,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=destinatarios
    )
    
    # Adiciona anexo se fornecido
    if anexo and anexo_content:
        email.attach(anexo, anexo_content, anexo_mimetype or 'application/octet-stream')
    
    # Tentativas de envio
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Tenta enviar o email
            resultado = email.send(fail_silently=False)
            
            if resultado > 0:
                if settings.EMAIL_DEBUG:
                    logger.info(f"Email enviado com sucesso para {destinatarios}")
                return True
            else:
                logger.warning(f"Email não foi enviado. Resultado: {resultado}")
                retry_count += 1
                
        except SMTPException as e:
            logger.error(f"Erro SMTP ao enviar email: {str(e)}")
            retry_count += 1
            
        except socket.error as e:
            logger.error(f"Erro de conexão ao servidor de email: {str(e)}")
            retry_count += 1
            
        except Exception as e:
            logger.error(f"Erro desconhecido ao enviar email: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            retry_count += 1
    
    logger.error(f"Falha ao enviar email após {max_retries} tentativas")
    return False

def verificar_configuracao_email():
    """
    Verifica se as configurações de email estão funcionando
    """
    try:
        # Verifica se o host é acessível
        if settings.EMAIL_HOST != 'localhost':
            # Tenta conectar ao servidor
            socket.create_connection((settings.EMAIL_HOST, settings.EMAIL_PORT), timeout=5)
            logger.info(f"Conexão bem-sucedida ao servidor de email {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        else:
            logger.info("Usando servidor local, pulando teste de conexão")
            
        # Tenta enviar um email simples
        resultado = send_mail(
            subject="Teste de Configuração de Email",
            message="Este é um email de teste automático para verificar as configurações.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['contato@agromarkers.com.br'],
            fail_silently=False
        )
        
        if resultado > 0:
            logger.info("✅ Teste de email enviado com sucesso!")
            return True
        else:
            logger.error("❌ Falha no teste de email!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erro ao verificar configuração de email: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
