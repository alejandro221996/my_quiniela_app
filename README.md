# 🏆 Sistema de Quinielas Django

Un sistema completo de quinielas deportivas desarrollado en Django, optimizado para Liga MX con funcionalidades avanzadas de gestión de apuestas, rankings y estadísticas en tiempo real.

## 🚀 Características Principales

### ⚽ **Gestión de Quinielas**
- Creación y administración de quinielas personalizadas
- Sistema de códigos de acceso únicos
- Participación múltiple en diferentes quinielas
- Dashboard unificado con métricas avanzadas

### 📊 **Sistema de Estadísticas**
- Estadísticas personales detalladas por usuario
- Rankings globales y por quiniela
- Componentes reutilizables para visualización de datos
- Cache optimizado para rendimiento superior

### 🎯 **Sistema de Apuestas**
- Apuestas en tiempo real con validación automática
- Cálculo automático de puntos
- Historial completo de apuestas
- Predicciones con sistema de puntuación

### 🔧 **Características Técnicas**
- **Performance**: Sistema de cache avanzado con invalidación automática
- **SEO**: URLs amigables con slugs y breadcrumbs
- **Responsive**: Diseño mobile-first con Tailwind CSS
- **API**: Endpoints para integración con datos externos
- **Testing**: Suite completa de tests organizados por módulo
- **Scheduled Jobs**: Actualización automática de resultados con cron
- **Logging**: Sistema robusto de logs con rotación automática

## 📁 **Estructura del Proyecto**

```
QuinielaDjango/
├── 📊 quinielas/              # App principal
├── 👥 accounts/               # Gestión de usuarios
├── 🔌 api_mock_app/          # API mock para datos
├── 📄 templates/             # Templates Django
├── 🎨 static/               # Archivos estáticos
├── 📚 docs/                 # Documentación
├── 🛠️ scripts/             # Scripts de utilidad
├── 📊 data/                 # Scripts de datos y demo
└── 📁 logs/                 # Logs del sistema
```

---

## 🛠️ Tecnologías Utilizadas

- **Backend**: Django 5.0+, Python 3.11+
- **Frontend**: Tailwind CSS, JavaScript ES6+
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **Cache**: Django Cache Framework (LocMemCache/Redis)
- **Testing**: Django TestCase, Coverage
- **API**: Django REST Framework (endpoints mock)

---

## 📦 Instalación y Configuración

### 1. **Requisitos Previos**
```bash
- Python 3.11+
- pip
- virtualenv (recomendado)
```

### 2. **Instalación**
```bash
# Clonar el repositorio
git clone <repository-url>
cd QuinielaDjango

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Cargar datos de ejemplo (opcional)
python manage.py loaddata fixtures/sample_data.json
```

### 3. **Ejecutar el Servidor de Desarrollo**
```bash
python manage.py runserver
```

El sistema estará disponible en: `http://localhost:8000`

---

## 🏗️ Estructura del Proyecto

```
QuinielaDjango/
├── quinielas/                    # App principal
│   ├── models.py                 # Modelos de datos
│   ├── views.py                  # Vistas y lógica de negocio
│   ├── forms.py                  # Formularios
│   ├── urls.py                   # Configuración de URLs
│   ├── cache_optimizations.py    # Sistema de cache
│   ├── signals.py                # Invalidación automática de cache
│   └── templatetags/             # Template tags personalizados
│       ├── stats_components.py   # Componentes de estadísticas
│       └── navigation_tags.py    # Sistema de navegación
├── accounts/                     # Sistema de autenticación
├── api_mock_app/                 # API mock para datos externos
├── templates/                    # Templates HTML
│   ├── components/               # Componentes reutilizables
│   └── quinielas/               # Templates específicos
├── static/                       # Archivos estáticos
└── media/                       # Archivos de usuario
```

---

## 🎮 Uso del Sistema

### **Para Usuarios**
1. **Registro**: Crear cuenta o registrarse con código de quiniela
2. **Participar**: Unirse a quinielas existentes o crear nuevas
3. **Apostar**: Realizar predicciones en partidos disponibles
4. **Seguimiento**: Revisar estadísticas y posición en rankings

### **Para Administradores**
1. **Panel Admin**: `http://localhost:8000/admin/`
2. **Gestión de Partidos**: Crear y actualizar partidos
3. **Gestión de Usuarios**: Administrar perfiles y permisos
4. **Monitoreo**: Revisar estadísticas del sistema

---

## 📊 Optimizaciones de Rendimiento

### **Sistema de Cache Implementado**
- **Estadísticas de Usuario**: Cache de 5 minutos
- **Ranking Global**: Cache de 10 minutos  
- **Próximos Partidos**: Cache de 5 minutos
- **Invalidación Automática**: Via signals de Django

### **Optimizaciones de Base de Datos**
- `select_related()` y `prefetch_related()` en consultas críticas
- Agregaciones SQL para rankings
- Índices optimizados en campos de búsqueda frecuente

### **Comandos de Mantenimiento**
```bash
# Limpiar cache manualmente
python manage.py clear_cache --type all

# Monitoreo de performance (en desarrollo)
# Activar MONITOR_PERFORMANCE = True en settings.py
```

---

## 🧪 Testing

### **Ejecutar Tests**
```bash
# Todos los tests
python manage.py test

# Tests específicos por app
python manage.py test quinielas
python manage.py test accounts

# Con coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Genera reporte HTML
```

### **Suite de Tests Incluida**
- ✅ Tests de modelos y validaciones
- ✅ Tests de vistas y autenticación  
- ✅ Tests de API endpoints
- ✅ Tests de formularios
- ✅ Tests de sistema de cache

---

## ⏰ **Scheduled Jobs para Actualización Automática**

El sistema incluye scheduled jobs para actualizar resultados automáticamente:

```bash
# Instalar cron jobs
python manage.py scheduled_jobs install

# Ver estado
python manage.py scheduled_jobs status

# Probar funcionamiento
python manage.py scheduled_jobs test

# Ver logs
python manage.py scheduled_jobs logs

# Desinstalar
python manage.py scheduled_jobs uninstall
```

### **Horarios Configurados:**
- ⏰ **Cada 30 min** (9:00-23:00): Verificación rápida
- 🕙 **Cada 2 horas**: Verificación detallada  
- 🌙 **23:00 diario**: Verificación completa

📚 **Documentación completa**: [`docs/SCHEDULED_JOBS_README.md`](docs/SCHEDULED_JOBS_README.md)

---

## 🎯 Personalización del Sistema de Puntos

Modifica el método `calcular_puntos()` en `quinielas/models.py`:

```python
def calcular_puntos(self):
    if not self.partido.finalizado:
        return 0
    
    # Resultado exacto: 3 puntos
    if (self.goles_local_apostados == self.partido.goles_local and 
        self.goles_visitante_apostados == self.partido.goles_visitante):
        return 3
    
    # Resultado correcto (ganador): 1 punto
    diferencia_real = self.partido.goles_local - self.partido.goles_visitante
    diferencia_apostada = self.goles_local_apostados - self.goles_visitante_apostados
    
    if diferencia_real > 0 and diferencia_apostada > 0:  # Ambos predicen local
        return 1
    elif diferencia_real < 0 and diferencia_apostada < 0:  # Ambos predicen visitante
        return 1
    elif diferencia_real == 0 and diferencia_apostada == 0:  # Ambos predicen empate
        return 1
    
    return 0
```

---

## 🤝 Contribución

1. Fork el proyecto
2. Crear branch de feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

---

## 📄 Licencia

MIT License - ver archivo LICENSE para detalles.

---

## ✅ Estado del Proyecto

**🚀 VERSIÓN 1.0 - LISTA PARA PRODUCCIÓN**

- [x] Funcionalidades core implementadas
- [x] Sistema de cache optimizado
- [x] Tests completos
- [x] Documentación completa
- [x] Configuración de producción lista
- [x] Performance optimizado

**¡El sistema está listo para ser desplegado en producción!** 🚀
