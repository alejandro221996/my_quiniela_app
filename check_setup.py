#!/usr/bin/env python3
"""
Script de verificación simple para My Quiniela App
Verifica que el sistema esté configurado correctamente después del bug fix
"""

import os
import sys
from pathlib import Path

def print_header(text):
    """Imprime un header formateado"""
    print(f"\n{'='*50}")
    print(f"  {text}")
    print(f"{'='*50}")

def print_success(text):
    """Imprime un mensaje de éxito"""
    print(f"✅ {text}")

def print_error(text):
    """Imprime un mensaje de error"""
    print(f"❌ {text}")

def print_warning(text):
    """Imprime un mensaje de advertencia"""
    print(f"⚠️  {text}")

def print_info(text):
    """Imprime información"""
    print(f"ℹ️  {text}")

def check_django_installation():
    """Verificar si Django está instalado"""
    try:
        import django
        print_success(f"Django instalado: {django.get_version()}")
        return True
    except ImportError:
        print_error("Django no está instalado")
        print_info("Ejecuta: pip install -r requirements.txt")
        return False

def check_project_files():
    """Verificar archivos importantes del proyecto"""
    important_files = [
        'manage.py',
        'requirements.txt',
        'accounts/forms.py',
        'accounts/models.py',
        'accounts/views.py',
        'github_automation.py',
        'mcp.json',
        '.gitignore'
    ]

    missing_files = []
    for file_path in important_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print_error(f"Archivos faltantes: {', '.join(missing_files)}")
        return False
    else:
        print_success("Todos los archivos importantes están presentes")
        return True

def check_env_configuration():
    """Verificar configuración de entorno"""
    env_file = Path('.env')

    if not env_file.exists():
        print_warning("Archivo .env no encontrado")
        print_info("Crea un archivo .env con:")
        print_info("  GITHUB_TOKEN=tu_token_aqui")
        print_info("  GITHUB_OWNER=alejandro221996")
        print_info("  GITHUB_REPO=my_quiniela_app")
        return False
    else:
        print_success("Archivo .env encontrado")

        # Verificar variables básicas
        try:
            with open('.env', 'r') as f:
                content = f.read()

            required_vars = ['GITHUB_TOKEN', 'GITHUB_OWNER', 'GITHUB_REPO']
            missing_vars = []

            for var in required_vars:
                if f"{var}=" not in content:
                    missing_vars.append(var)

            if missing_vars:
                print_warning(f"Variables faltantes en .env: {', '.join(missing_vars)}")
                return False
            else:
                print_success("Variables básicas configuradas en .env")
                return True

        except Exception as e:
            print_error(f"Error leyendo .env: {e}")
            return False

def check_django_project():
    """Verificar configuración básica de Django"""
    if not check_django_installation():
        return False

    try:
        import django
        from django.conf import settings
        from django.core.management import execute_from_command_line

        # Intentar importar configuraciones
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quinielas_project.settings')
        django.setup()

        print_success("Configuración de Django válida")
        return True

    except Exception as e:
        print_error(f"Error en configuración Django: {e}")
        return False

def check_bug_fix_implementation():
    """Verificar que el bug fix esté implementado"""
    print_info("Verificando implementación del bug fix...")

    # Verificar forms.py
    forms_file = Path('accounts/forms.py')
    if forms_file.exists():
        try:
            with open(forms_file, 'r') as f:
                content = f.read()

            if 'ExtendedUserCreationForm' in content:
                print_success("Formulario extendido implementado")
            else:
                print_error("Formulario extendido no encontrado")
                return False
        except Exception as e:
            print_error(f"Error leyendo forms.py: {e}")
            return False
    else:
        print_error("Archivo accounts/forms.py no encontrado")
        return False

    # Verificar models.py actualizado
    models_file = Path('accounts/models.py')
    if models_file.exists():
        try:
            with open(models_file, 'r') as f:
                content = f.read()

            if 'logging' in content and 'logger' in content:
                print_success("Logging implementado en models.py")
            else:
                print_warning("Logging no encontrado en models.py")
        except Exception as e:
            print_error(f"Error leyendo models.py: {e}")
            return False

    # Verificar views.py actualizado
    views_file = Path('accounts/views.py')
    if views_file.exists():
        try:
            with open(views_file, 'r') as f:
                content = f.read()

            if 'ExtendedUserCreationForm' in content and 'transaction.atomic' in content:
                print_success("Vista de registro mejorada implementada")
            else:
                print_warning("Mejoras de vista no completamente implementadas")
        except Exception as e:
            print_error(f"Error leyendo views.py: {e}")
            return False

    return True

def check_github_automation():
    """Verificar herramientas de GitHub automation"""
    if Path('github_automation.py').exists():
        print_success("GitHub automation script disponible")

        # Verificar que no tenga tokens hardcoded
        try:
            with open('github_automation.py', 'r') as f:
                content = f.read()

            if 'github_pat_' in content:
                print_error("⚠️  PELIGRO: Token hardcoded detectado en github_automation.py")
                return False
            else:
                print_success("GitHub automation script seguro (sin tokens hardcoded)")
        except Exception as e:
            print_warning(f"No se pudo verificar contenido: {e}")

        return True
    else:
        print_error("GitHub automation script no encontrado")
        return False

def check_mcp_configuration():
    """Verificar configuración MCP"""
    if Path('mcp.json').exists():
        try:
            import json
            with open('mcp.json', 'r') as f:
                config = json.load(f)

            if 'mcpServers' in config and 'github' in config['mcpServers']:
                print_success("Configuración MCP válida")

                # Verificar que use variable de entorno
                github_config = config['mcpServers']['github']
                if 'env' in github_config:
                    token_value = github_config['env'].get('GITHUB_PERSONAL_ACCESS_TOKEN', '')
                    if token_value.startswith('${') or token_value == 'your_github_token_here':
                        print_success("MCP usa variables de entorno (seguro)")
                    elif token_value.startswith('github_pat_'):
                        print_error("⚠️  PELIGRO: Token hardcoded en mcp.json")
                        return False
                    else:
                        print_success("Configuración MCP segura")

                return True
            else:
                print_error("Configuración MCP incompleta")
                return False

        except Exception as e:
            print_error(f"Error validando mcp.json: {e}")
            return False
    else:
        print_error("Archivo mcp.json no encontrado")
        return False

def main():
    """Función principal"""
    print_header("🔍 Verificación de My Quiniela App")
    print_info("Verificando configuración después del bug fix...")

    checks = [
        ("📁 Archivos del proyecto", check_project_files),
        ("🔧 Configuración de entorno", check_env_configuration),
        ("🐍 Django", check_django_project),
        ("✅ Bug fix implementado", check_bug_fix_implementation),
        ("🤖 GitHub automation", check_github_automation),
        ("🔗 Configuración MCP", check_mcp_configuration)
    ]

    results = []
    for name, check_func in checks:
        print(f"\n📋 Verificando: {name}")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Error en verificación: {e}")
            results.append((name, False))

    # Resumen final
    print_header("📊 Resumen de Verificación")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")

    print(f"\n📈 Resultado: {passed}/{total} verificaciones exitosas")

    if passed == total:
        print_success("🎉 ¡Todo está configurado correctamente!")
        print_info("Tu aplicación está lista para usar")
        print_info("\n🚀 Próximos pasos:")
        print_info("  1. python manage.py runserver")
        print_info("  2. Visita: http://localhost:8000/accounts/registro/")
        print_info("  3. Prueba el nuevo sistema de registro")
    elif passed >= total * 0.8:
        print_warning("⚠️  Configuración mayormente completa")
        print_info("Algunas funcionalidades pueden estar limitadas")
    else:
        print_error("❌ Se requiere atención en múltiples áreas")
        print_info("Revisa los errores anteriores")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
