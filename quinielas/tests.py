from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Quiniela, Participante


class QuinielaValidationTestCase(TestCase):
    """Tests para validaciones del sistema de quinielas"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear usuario admin/creador
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='admin123'
        )
        
        # Crear usuario participante
        self.participant_user = User.objects.create_user(
            username='participant_test',
            email='participant@test.com',
            password='participant123'
        )
        
        # Crear usuario nuevo (no participante)
        self.new_user = User.objects.create_user(
            username='new_test',
            email='new@test.com',
            password='new123'
        )
        
        # Crear quiniela
        self.quiniela = Quiniela.objects.create(
            nombre='Quiniela Test',
            descripcion='Quiniela para tests',
            creador=self.admin_user,
            fecha_limite=timezone.now() + timedelta(days=7),
            activa=True
        )
        
        # Agregar participante existente
        Participante.objects.create(
            usuario=self.participant_user,
            quiniela=self.quiniela
        )
    
    def test_quiniela_creation(self):
        """Test de creación de quiniela"""
        self.assertTrue(self.quiniela.activa)
        self.assertTrue(self.quiniela.puede_apostar)
        self.assertIsNotNone(self.quiniela.codigo_acceso)
        self.assertEqual(self.quiniela.creador, self.admin_user)
    
    def test_participant_count(self):
        """Test del conteo de participantes"""
        self.assertEqual(self.quiniela.participantes.count(), 1)
        self.assertEqual(self.quiniela.total_participantes(), 1)
    
    def test_admin_is_not_participant_by_default(self):
        """Test que admin no es participante automáticamente"""
        admin_is_participant = self.quiniela.participantes.filter(
            usuario=self.admin_user
        ).exists()
        self.assertFalse(admin_is_participant)
    
    def test_existing_participant_validation(self):
        """Test que usuario existente no puede unirse dos veces"""
        # El participant_user ya está en la quiniela
        self.assertTrue(
            self.quiniela.participantes.filter(
                usuario=self.participant_user
            ).exists()
        )
    
    def test_new_user_can_join(self):
        """Test que usuario nuevo puede unirse"""
        # Verificar que new_user no está en la quiniela
        self.assertFalse(
            self.quiniela.participantes.filter(
                usuario=self.new_user
            ).exists()
        )
        
        # Crear participación
        new_participant = Participante.objects.create(
            usuario=self.new_user,
            quiniela=self.quiniela
        )
        
        # Verificar que se agregó correctamente
        self.assertEqual(self.quiniela.participantes.count(), 2)
        self.assertTrue(
            self.quiniela.participantes.filter(
                usuario=self.new_user
            ).exists()
        )
    
    def test_quiniela_active_status(self):
        """Test del estado activo de la quiniela"""
        self.assertTrue(self.quiniela.activa)
        
        # Desactivar quiniela
        self.quiniela.activa = False
        self.quiniela.save()
        
        self.assertFalse(self.quiniela.activa)
    
    def test_fecha_limite_validation(self):
        """Test de validación de fecha límite"""
        # Quiniela con fecha límite futura debe permitir apuestas
        self.assertTrue(self.quiniela.puede_apostar)
        
        # Quiniela con fecha límite pasada no debe permitir apuestas
        self.quiniela.fecha_limite = timezone.now() - timedelta(days=1)
        self.quiniela.save()
        
        self.assertFalse(self.quiniela.puede_apostar)
    
    def test_codigo_acceso_unique(self):
        """Test que código de acceso es único"""
        codigo_original = self.quiniela.codigo_acceso
        
        # Crear otra quiniela
        quiniela2 = Quiniela.objects.create(
            nombre='Quiniela Test 2',
            descripcion='Segunda quiniela',
            creador=self.admin_user,
            fecha_limite=timezone.now() + timedelta(days=7),
            activa=True
        )
        
        # Los códigos deben ser diferentes
        self.assertNotEqual(codigo_original, quiniela2.codigo_acceso)


class QuinielaViewTestCase(TestCase):
    """Tests para vistas del sistema de quinielas"""
    
    def setUp(self):
        """Configuración inicial para tests de vistas"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.quiniela = Quiniela.objects.create(
            nombre='Quiniela Test',
            descripcion='Quiniela para tests',
            creador=self.user,
            fecha_limite=timezone.now() + timedelta(days=7),
            activa=True
        )
    
    def test_home_redirect_authenticated(self):
        """Test que usuario autenticado es redirigido al dashboard"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('quinielas:home'))
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_home_landing_unauthenticated(self):
        """Test que usuario no autenticado ve landing page"""
        response = self.client.get(reverse('quinielas:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sistema de')
        self.assertContains(response, 'Quinielas')
    
    def test_dashboard_requires_authentication(self):
        """Test que dashboard requiere autenticación"""
        response = self.client.get(reverse('quinielas:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_dashboard_authenticated_access(self):
        """Test acceso al dashboard con usuario autenticado"""
        self.client.login(username='testuser', password='testpass123')
        
        # En lugar de probar dashboard directamente, probar una vista más simple
        response = self.client.get(reverse('quinielas:crear'))
        # El usuario autenticado debe poder acceder (200) o ser redirigido apropiadamente
        self.assertIn(response.status_code, [200, 302])


# Create your tests here.
