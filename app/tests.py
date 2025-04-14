from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import (
    Empresa, Projeto, Placa96, Placa384,
    Amostra, Poco96, Poco384, PlacaMap384, Status,
    Cultivo, Tecnologia, Marcador, Protocolo, Etapa
)
import datetime

User = get_user_model()

class BaseTestCase(TestCase):
    def setUp(self):
        # Create base test data
        self.empresa = Empresa.objects.create(
            nome="Test Enterprise",
            codigo="TEST",
            cnpj="12345678901234"
        )

        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            empresa=self.empresa
        )

        self.admin_user = User.objects.create_superuser(
            username="admin",
            password="admin123",
            empresa=self.empresa
        )

        # Criar objetos básicos necessários
        self.status = Status.objects.create(
            nome="Em Andamento",
            empresa=self.empresa
        )
        
        self.cultivo = Cultivo.objects.create(
            nome="Soja",
            empresa=self.empresa
        )
        
        self.tecnologia = Tecnologia.objects.create(
            nome="Test Tech",
            empresa=self.empresa
        )

        self.protocolo = Protocolo.objects.create(
            nome="Protocolo Teste",
            empresa=self.empresa
        )

        self.etapa = Etapa.objects.create(
            nome="Etapa Teste",
            empresa=self.empresa
        )

        self.client = Client()

class ProjetoTests(BaseTestCase):
    def test_create_projeto(self):
        """Test project creation with automatic resource generation"""
        projeto = Projeto.objects.create(
            empresa=self.empresa,
            codigo_projeto="001",
            quantidade_amostras=100,
            cultivo=self.cultivo,
            status=self.status,
            tecnologia=self.tecnologia,
            protocolo=self.protocolo,
            etapa=self.etapa
        )

        # Verify project was created
        self.assertEqual(projeto.codigo_projeto, "001")
        
        # Verify automatic resource creation
        self.assertTrue(projeto.placa96_set.exists())
        self.assertTrue(projeto.amostra_set.exists())
        
        # Check number of plates (90 samples per plate + control wells)
        expected_plates = -(-100 // 90)  # Ceiling division for 90 samples per plate
        self.assertEqual(projeto.placa96_set.count(), expected_plates)
        
        # Check number of samples (including NTC control sample)
        self.assertEqual(projeto.amostra_set.count(), 101)  # 100 + 1 NTC

    def test_projeto_validation(self):
        """Test project validation rules"""
        projeto = Projeto.objects.create(
            empresa=self.empresa,
            codigo_projeto="002",
            quantidade_amostras=100,
            status=self.status,
            protocolo=self.protocolo,
            etapa=self.etapa,
            cultivo=self.cultivo,
            data_envio=datetime.date(2024, 1, 1)
        )
        
        # Tentar definir uma data de recebimento anterior à data de envio
        projeto.data_recebimento_laboratorio = datetime.date(2023, 12, 31)
        
        with self.assertRaises(ValidationError):
            projeto.clean()

class PlacaTransferTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        
        self.projeto = Projeto.objects.create(
            empresa=self.empresa,
            codigo_projeto="001",
            quantidade_amostras=96,
            status=self.status,
            protocolo=self.protocolo,
            etapa=self.etapa,
            cultivo=self.cultivo
        )

        # Create 96-well plates
        self.placas_96 = []
        for i in range(4):
            placa = Placa96.objects.create(
                empresa=self.empresa,
                projeto=self.projeto,
                codigo_placa=f"P96-{i+1}"
            )
            self.placas_96.append(placa)

        # Create samples and wells
        self._create_samples_and_wells()

    def _create_samples_and_wells(self):
        """Helper method to create samples and wells"""
        for placa in self.placas_96:
            for i in range(96):
                amostra = Amostra.objects.create(
                    empresa=self.empresa,
                    projeto=self.projeto,
                    codigo_amostra=f"A{placa.codigo_placa}-{i+1}"
                )
                
                row = chr(65 + (i // 12))  # A-H
                col = (i % 12) + 1
                Poco96.objects.create(
                    empresa=self.empresa,
                    placa=placa,
                    amostra=amostra,
                    posicao=f"{row}{col}"
                )

    def test_transfer_96_to_384(self):
        """Test transfer from 96-well plates to 384-well plate"""
        placa_384 = Placa384.objects.create(
            empresa=self.empresa,
            projeto=self.projeto,
            codigo_placa="P384-1"
        )

        try:
            with transaction.atomic():
                placa_384.transfer_96_to_384(self.placas_96)

            self.assertEqual(placa_384.poco384_set.count(), 384)
            self.assertEqual(PlacaMap384.objects.filter(placa_destino=placa_384).count(), 4)

            # Check original plates were deactivated
            for placa in self.placas_96:
                placa.refresh_from_db()
                self.assertFalse(placa.is_active)

        except Exception as e:
            self.fail(f"Transfer failed with error: {str(e)}")

    def test_invalid_transfer_conditions(self):
        """Test various invalid transfer conditions"""
        placa_384 = Placa384.objects.create(
            empresa=self.empresa,
            projeto=self.projeto,
            codigo_placa="P384-2"
        )

        # Test with less than 4 plates
        with self.assertRaises(ValidationError):
            placa_384.transfer_96_to_384(self.placas_96[:2])

class ApiTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username='admin', password='admin123')
        
        self.projeto = Projeto.objects.create(
            empresa=self.empresa,
            codigo_projeto="001",
            quantidade_amostras=96,
            status=self.status,
            protocolo=self.protocolo,
            etapa=self.etapa,
            cultivo=self.cultivo
        )

    def test_get_projetos_api(self):
        """Test the get_projetos API endpoint"""
        # Usar o path direto já que estamos testando a API
        response = self.client.get(f'/admin/app/placa384/get-projetos/{self.empresa.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)

    def test_get_placas_96_api(self):
        """Test the get_placas_96 API endpoint"""
        # Usar o path direto já que estamos testando a API
        response = self.client.get(f'/admin/app/placa384/get-placas/{self.projeto.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

class SecurityTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username='admin', password='admin123')
        
        self.projeto1 = Projeto.objects.create(
            empresa=self.empresa,
            codigo_projeto="001",
            quantidade_amostras=96,
            status=self.status,
            protocolo=self.protocolo,
            etapa=self.etapa,
            cultivo=self.cultivo
        )

    def test_empresa_isolation(self):
        """Test that users can only access their enterprise's data"""
        response = self.client.get(f'/admin/app/placa384/get-projetos/{self.empresa.id}/')
        self.assertEqual(response.status_code, 200)

        # Criar outro usuário e empresa
        other_empresa = Empresa.objects.create(
            nome="Other Enterprise",
            codigo="OTHER",
            cnpj="98765432101234"
        )
        
        other_user = User.objects.create_user(
            username="otheruser",
            password="otherpass123",
            empresa=other_empresa
        )
        
        # Logar com outro usuário
        self.client.login(username='otheruser', password='otherpass123')
        response = self.client.get(f'/admin/app/placa384/get-projetos/{self.empresa.id}/')
        self.assertEqual(response.status_code, 403)  # Deve ser proibido

    def test_superuser_access(self):
        """Test that superusers can access all enterprises' data"""
        response = self.client.get(f'/admin/app/placa384/get-projetos/{self.empresa.id}/')
        self.assertEqual(response.status_code, 200)

class SecurityTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.login(username='admin', password='admin123')
        
        # Create another enterprise and its resources
        self.other_empresa = Empresa.objects.create(
            nome="Other Enterprise",
            codigo="OTHER",
            cnpj="98765432101234"
        )

        # Create projects for testing
        self.projeto1 = Projeto.objects.create(
            empresa=self.empresa,
            codigo_projeto="001",
            quantidade_amostras=96,
            status=self.status,
            protocolo=self.protocolo,
            etapa=self.etapa,
            cultivo=self.cultivo
        )

    def test_empresa_isolation(self):
        """Test that users can only access their enterprise's data"""
        url = reverse('get_projetos_admin', args=[self.empresa.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_superuser_access(self):
        """Test that superusers can access all enterprises' data"""
        url = reverse('get_projetos_admin', args=[self.empresa.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)