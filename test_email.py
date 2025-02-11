import os
import django
import smtplib
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configurar o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SGL.settings')
django.setup()

def test_smtp_direct():
    """
    Testa conexão SMTP direta com o servidor
    """
    print("\n1. Testando conexão SMTP direta...")
    try:
        # Iniciar conexão
        print(f"Conectando a {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        smtp = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        
        # Iniciar TLS
        print("Iniciando TLS...")
        smtp.starttls()
        
        # Login
        print("Tentando login...")
        smtp.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        print("Login realizado com sucesso!")
        
        # Fechar conexão
        smtp.quit()
        print("Teste de conexão SMTP concluído com sucesso!")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("ERRO: Falha na autenticação. Verifique usuário e senha.")
        return False
    except Exception as e:
        print(f"ERRO: {str(e)}")
        return False

def test_django_email():
    """
    Testa o envio de email usando o framework Django
    """
    print("\n2. Testando envio de email via Django...")
    try:
        # Preparar email
        subject = 'Teste de Email - Django SGL'
        message = 'Este é um email de teste do sistema SGL.'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = ['contato@agromarkers.com.br']  # Substitua pelo seu email
        
        print(f"De: {from_email}")
        print(f"Para: {recipient_list}")
        
        # Enviar email
        result = send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        
        if result == 1:
            print("Email enviado com sucesso via Django!")
            return True
        else:
            print("Falha no envio do email via Django.")
            return False
            
    except Exception as e:
        print(f"ERRO ao enviar email via Django: {str(e)}")
        return False

def test_email_with_attachment():
    """
    Testa o envio de email com anexo
    """
    print("\n3. Testando envio de email com anexo...")
    try:
        # Criar email
        email = EmailMessage(
            subject='Teste de Email com Anexo - Django SGL',
            body='Este é um email de teste com anexo do sistema SGL.',
            from_email=settings.EMAIL_HOST_USER,
            to=['contato@agromarkers.com.br']  # Substitua pelo seu email
        )
        
        # Criar arquivo de teste
        test_file_path = 'test_attachment.txt'
        with open(test_file_path, 'w') as f:
            f.write('Este é um arquivo de teste para anexo.')
        
        # Anexar arquivo
        with open(test_file_path, 'rb') as f:
            email.attach('test_attachment.txt', f.read(), 'text/plain')
        
        # Enviar email
        email.send(fail_silently=False)
        
        # Limpar arquivo de teste
        os.remove(test_file_path)
        
        print("Email com anexo enviado com sucesso!")
        return True
        
    except Exception as e:
        print(f"ERRO ao enviar email com anexo: {str(e)}")
        return False

def print_email_settings():
    """
    Imprime as configurações de email atuais
    """
    print("\nConfigurações de Email:")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD)}")

def run_all_tests():
    """
    Executa todos os testes
    """
    print("=== Iniciando testes de email ===")
    print_email_settings()
    
    # Executar testes
    tests = [
        test_smtp_direct,
        test_django_email,
        test_email_with_attachment
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"Erro ao executar teste {test.__name__}: {str(e)}")
            results.append(False)
    
    # Relatório final
    print("\n=== Relatório Final ===")
    print(f"Testes executados: {len(tests)}")
    print(f"Testes bem sucedidos: {sum(results)}")
    print(f"Testes falhos: {len(results) - sum(results)}")
    
    if all(results):
        print("\nTodos os testes passaram! O sistema de email está funcionando corretamente.")
    else:
        print("\nAlguns testes falharam. Verifique as mensagens de erro acima.")

if __name__ == "__main__":
    run_all_tests()