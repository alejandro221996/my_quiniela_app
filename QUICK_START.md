# 🚀 Quick Start - My Quiniela App

Guía rápida para configurar y probar el sistema después del bug fix.

## ⚡ Instalación Rápida (5 minutos)

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno
Crea archivo `.env` en la raíz del proyecto:
```bash
# GitHub Configuration (para automation)
GITHUB_TOKEN=tu_token_github_aqui
GITHUB_OWNER=alejandro221996
GITHUB_REPO=my_quiniela_app

# Django Configuration
DEBUG=True
SECRET_KEY=django-insecure-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3
```

### 3. Configurar base de datos
```bash
python manage.py migrate
python manage.py fix_user_profiles --dry-run  # Verificar perfiles
python manage.py createsuperuser              # Opcional
```

### 4. Ejecutar servidor
```bash
python manage.py runserver
```

## 🧪 Probar el Bug Fix

### Ir a registro:
http://localhost:8000/accounts/registro/

### Probar nuevo formulario:
- ✅ Nombre y apellido (requeridos)
- ✅ Email único (requerido)
- ✅ Tipo de usuario (Participante/Organizador)
- ✅ Código de invitación (opcional)
- ✅ Validaciones mejoradas
- ✅ Auto-login después del registro

## 🔧 Verificar Configuración

```bash
python check_setup.py
```

Este script verifica:
- ✅ Django instalado
- ✅ Archivos importantes presentes
- ✅ Bug fix implementado
- ✅ Configuración segura (sin tokens hardcoded)

## 🤖 GitHub Automation

```bash
# Ver info del repositorio
python github_automation.py info

# Crear PR automático (requiere .env configurado)
python github_automation.py quick "nueva funcionalidad"
```

## 📋 VS Code Tasks

1. `Ctrl+Shift+P` (o `Cmd+Shift+P`)
2. "Tasks: Run Task"
3. Seleccionar:
   - **⚽ Quick PR** - Crear PR automático
   - **🚀 Django Runserver** - Ejecutar servidor
   - **⚙️ Django Migrate** - Ejecutar migraciones

## ❌ Problemas Comunes

### "ModuleNotFoundError: No module named 'django'"
```bash
pip install -r requirements.txt
```

### "GITHUB_TOKEN no encontrado"
Crear archivo `.env` con tu token de GitHub.

### Perfiles de usuario faltantes
```bash
python manage.py fix_user_profiles --fix-all
```

## ✅ Issue #1 - SOLUCIONADO

**Problema original**: "Error assigning personal data on new user registration"

**Solución implementada**:
- ✅ Formulario extendido con todos los campos necesarios
- ✅ Transacciones atómicas para prevenir registros parciales
- ✅ Manejo robusto de errores con logging
- ✅ Validaciones completas (email único, formato username)
- ✅ Creación garantizada de perfiles de usuario
- ✅ Auto-login después del registro exitoso

## 🎯 Resultado

El sistema ahora captura y guarda correctamente **TODOS** los datos personales de usuarios nuevos:
- Nombre y apellido
- Email
- Tipo de usuario (Participante/Organizador)
- Código de invitación (si aplica)
- Perfil de usuario asociado automáticamente

¡Tu aplicación de quinielas está lista! ⚽🎉