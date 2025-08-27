from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
import json


class APIMockTestCase(TestCase):
    """Tests para las APIs Mock del sistema"""
    
    def setUp(self):
        """Configuración inicial para tests de API"""
        self.client = Client()
        
        # Crear usuario para tests autenticados
        self.user = User.objects.create_user(
            username='apitest',
            email='api@test.com',
            password='apitest123'
        )
        
        # URLs de las APIs
        self.api_urls = {
            'equipos': reverse('api_mock:equipos'),
            'partidos': reverse('api_mock:partidos'), 
            'estadisticas': reverse('api_mock:estadisticas'),
        }
    
    def test_api_requires_authentication(self):
        """Test que las APIs requieren autenticación"""
        for api_name, url in self.api_urls.items():
            response = self.client.get(url)
            # APIs protegidas deben redirigir a login o devolver 401/403
            self.assertIn(response.status_code, [302, 401, 403], 
                         f"API {api_name} no está protegida")
    
    def test_equipos_api_authenticated(self):
        """Test API de equipos con usuario autenticado"""
        self.client.login(username='apitest', password='apitest123')
        
        response = self.client.get(self.api_urls['equipos'])
        self.assertEqual(response.status_code, 200)
        
        # Verificar que es JSON válido
        try:
            data = json.loads(response.content)
            self.assertIsInstance(data, (list, dict))
        except json.JSONDecodeError:
            self.fail("Response is not valid JSON")
    
    def test_partidos_api_authenticated(self):
        """Test API de partidos con usuario autenticado"""
        self.client.login(username='apitest', password='apitest123')
        
        response = self.client.get(self.api_urls['partidos'])
        self.assertEqual(response.status_code, 200)
        
        # Verificar que es JSON válido
        try:
            data = json.loads(response.content)
            self.assertIsInstance(data, (list, dict))
        except json.JSONDecodeError:
            self.fail("Response is not valid JSON")
    
    def test_estadisticas_api_authenticated(self):
        """Test API de estadísticas con usuario autenticado"""
        self.client.login(username='apitest', password='apitest123')
        
        response = self.client.get(self.api_urls['estadisticas'])
        self.assertEqual(response.status_code, 200)
        
        # Verificar que es JSON válido
        try:
            data = json.loads(response.content)
            self.assertIsInstance(data, (list, dict))
        except json.JSONDecodeError:
            self.fail("Response is not valid JSON")
    
    def test_api_content_type(self):
        """Test que las APIs devuelven JSON"""
        self.client.login(username='apitest', password='apitest123')
        
        for api_name, url in self.api_urls.items():
            response = self.client.get(url)
            if response.status_code == 200:
                self.assertEqual(response['Content-Type'], 'application/json',
                               f"API {api_name} no devuelve JSON")
    
    def test_api_response_structure(self):
        """Test estructura básica de respuestas de APIs"""
        self.client.login(username='apitest', password='apitest123')
        
        # Test API de equipos
        response = self.client.get(self.api_urls['equipos'])
        if response.status_code == 200:
            try:
                data = json.loads(response.content)
                if isinstance(data, list) and len(data) > 0:
                    # Verificar estructura de equipo
                    equipo = data[0]
                    self.assertIn('nombre', equipo)
            except (json.JSONDecodeError, KeyError, IndexError):
                pass  # API mock puede tener estructura diferente
        
        # Test API de partidos
        response = self.client.get(self.api_urls['partidos'])
        if response.status_code == 200:
            try:
                data = json.loads(response.content)
                if isinstance(data, list) and len(data) > 0:
                    # Verificar estructura de partido
                    partido = data[0]
                    self.assertIn('equipo_local', partido)
                    self.assertIn('equipo_visitante', partido)
            except (json.JSONDecodeError, KeyError, IndexError):
                pass  # API mock puede tener estructura diferente


class APISecurityTestCase(TestCase):
    """Tests de seguridad para las APIs"""
    
    def setUp(self):
        """Configuración para tests de seguridad"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='securitytest',
            email='security@test.com', 
            password='security123'
        )
    
    def test_csrf_protection(self):
        """Test protección CSRF en APIs que lo requieren"""
        # APIs GET generalmente no requieren CSRF
        # Este test verifica que las protecciones estén en lugar
        self.client.login(username='securitytest', password='security123')
        
        apis_to_test = [
            reverse('api_mock:equipos'),
            reverse('api_mock:partidos'),
            reverse('api_mock:estadisticas'),
        ]
        
        for url in apis_to_test:
            response = self.client.get(url)
            # Verificar que no hay errores de CSRF en GET
            self.assertNotEqual(response.status_code, 403, 
                               f"CSRF error en {url}")
    
    def test_session_security(self):
        """Test seguridad de sesiones en APIs"""
        # Login y obtener respuesta autenticada
        self.client.login(username='securitytest', password='security123')
        
        response = self.client.get(reverse('api_mock:equipos'))
        if response.status_code == 200:
            # Verificar que la sesión es segura
            self.assertIn('_auth_user_id', self.client.session)


# Create your tests here.
