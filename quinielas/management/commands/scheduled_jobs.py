"""
Comando unificado para gestión de scheduled jobs
Combina funcionalidades de configuración y mantenimiento
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import subprocess
import sys
from pathlib import Path

class Command(BaseCommand):
    help = 'Gestión completa de scheduled jobs para actualización de resultados'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['install', 'uninstall', 'status', 'test', 'logs'],
            help='Acción a realizar'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Modo simulación para test'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        self.stdout.write(f"🔧 GESTIÓN DE SCHEDULED JOBS - {action.upper()}")
        self.stdout.write("=" * 50)
        
        if action == 'install':
            self.install_cron_jobs()
        elif action == 'uninstall':
            self.uninstall_cron_jobs()
        elif action == 'status':
            self.show_status()
        elif action == 'test':
            self.test_command(options.get('dry_run', False))
        elif action == 'logs':
            self.show_logs()
    
    def install_cron_jobs(self):
        """Instala cron jobs automáticamente"""
        self.stdout.write("📥 Instalando cron jobs...")
        
        project_dir = Path(settings.BASE_DIR)
        python_path = project_dir / '.venv' / 'bin' / 'python'
        manage_py = project_dir / 'manage.py'
        logs_dir = project_dir / 'logs'
        
        # Crear directorio de logs
        logs_dir.mkdir(exist_ok=True)
        
        # Crear script wrapper temporal
        wrapper_script = project_dir / 'temp_cron_wrapper.sh'
        wrapper_content = f"""#!/bin/bash
cd {project_dir}
{python_path} {manage_py} actualizar_resultados "$@"
"""
        
        with open(wrapper_script, 'w') as f:
            f.write(wrapper_content)
        
        os.chmod(wrapper_script, 0o755)
        
        # Configuración de crontab
        cron_lines = [
            f"# QUINIELAS AUTO-UPDATE",
            f"*/30 9-23 * * * {wrapper_script} --days-back=1 >> {logs_dir}/cron_resultados.log 2>&1",
            f"0 23 * * * {wrapper_script} --days-back=7 --verbose >> {logs_dir}/cron_diario.log 2>&1",
            f"# QUINIELAS AUTO-UPDATE END"
        ]
        
        try:
            # Obtener crontab actual
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            current_cron = result.stdout if result.returncode == 0 else ""
            
            # Filtrar líneas existentes
            filtered_lines = []
            skip = False
            for line in current_cron.split('\n'):
                if '# QUINIELAS AUTO-UPDATE' in line and not line.endswith('END'):
                    skip = True
                elif '# QUINIELAS AUTO-UPDATE END' in line:
                    skip = False
                    continue
                elif not skip and line.strip():
                    filtered_lines.append(line)
            
            # Agregar nuevas líneas
            new_cron = '\n'.join(filtered_lines + [''] + cron_lines + [''])
            
            # Aplicar nuevo crontab
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_cron)
            
            if process.returncode == 0:
                self.stdout.write(
                    self.style.SUCCESS("✅ Cron jobs instalados exitosamente!")
                )
                self.stdout.write(f"📁 Script wrapper: {wrapper_script}")
                self.stdout.write(f"📁 Logs en: {logs_dir}/")
            else:
                raise CommandError("Error instalando crontab")
                
        except Exception as e:
            raise CommandError(f"Error configurando cron: {str(e)}")
    
    def uninstall_cron_jobs(self):
        """Desinstala cron jobs"""
        self.stdout.write("🗑️  Desinstalando cron jobs...")
        
        try:
            # Obtener crontab actual
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode != 0:
                self.stdout.write("ℹ️  No hay crontab configurado")
                return
            
            current_cron = result.stdout
            
            # Filtrar líneas de quinielas
            filtered_lines = []
            skip = False
            for line in current_cron.split('\n'):
                if '# QUINIELAS AUTO-UPDATE' in line and not line.endswith('END'):
                    skip = True
                elif '# QUINIELAS AUTO-UPDATE END' in line:
                    skip = False
                    continue
                elif not skip and line.strip():
                    filtered_lines.append(line)
            
            # Aplicar crontab limpio
            new_cron = '\n'.join(filtered_lines)
            
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_cron)
            
            if process.returncode == 0:
                self.stdout.write(
                    self.style.SUCCESS("✅ Cron jobs desinstalados exitosamente!")
                )
                
                # Limpiar script wrapper temporal
                project_dir = Path(settings.BASE_DIR)
                wrapper_script = project_dir / 'temp_cron_wrapper.sh'
                if wrapper_script.exists():
                    wrapper_script.unlink()
                    self.stdout.write("🗑️  Script wrapper eliminado")
            else:
                raise CommandError("Error desinstalando crontab")
                
        except Exception as e:
            raise CommandError(f"Error desinstalando cron: {str(e)}")
    
    def show_status(self):
        """Muestra estado actual"""
        self.stdout.write("📊 Estado de scheduled jobs:")
        
        try:
            # Verificar crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            
            if result.returncode == 0 and 'QUINIELAS AUTO-UPDATE' in result.stdout:
                self.stdout.write("✅ Cron jobs instalados")
                
                # Mostrar líneas relevantes
                for line in result.stdout.split('\n'):
                    if 'actualizar_resultados' in line and not line.startswith('#'):
                        self.stdout.write(f"   📅 {line}")
                
                # Verificar logs recientes
                logs_dir = Path(settings.BASE_DIR) / 'logs'
                if (logs_dir / 'cron_resultados.log').exists():
                    self.stdout.write("\n📄 Últimas ejecuciones:")
                    try:
                        with open(logs_dir / 'cron_resultados.log', 'r') as f:
                            lines = f.readlines()[-3:]
                            for line in lines:
                                self.stdout.write(f"   {line.strip()}")
                    except:
                        pass
            else:
                self.stdout.write("❌ Cron jobs no instalados")
                self.stdout.write("💡 Ejecuta: python manage.py scheduled_jobs install")
                
        except Exception as e:
            self.stdout.write(f"❌ Error verificando estado: {str(e)}")
    
    def test_command(self, dry_run=True):
        """Prueba el comando de actualización"""
        self.stdout.write("🧪 Probando comando de actualización...")
        
        try:
            from django.core.management import call_command
            from io import StringIO
            
            output = StringIO()
            args = ['--verbose']
            if dry_run:
                args.append('--dry-run')
            
            call_command('actualizar_resultados', *args, stdout=output)
            
            # Mostrar salida
            for line in output.getvalue().split('\n')[:10]:
                if line.strip():
                    self.stdout.write(f"   {line}")
            
            self.stdout.write("✅ Comando probado exitosamente")
            
        except Exception as e:
            raise CommandError(f"Error probando comando: {str(e)}")
    
    def show_logs(self):
        """Muestra logs recientes"""
        self.stdout.write("📄 Logs de scheduled jobs:")
        
        logs_dir = Path(settings.BASE_DIR) / 'logs'
        
        for log_file in ['cron_resultados.log', 'cron_diario.log']:
            log_path = logs_dir / log_file
            if log_path.exists():
                self.stdout.write(f"\n📋 {log_file}:")
                try:
                    with open(log_path, 'r') as f:
                        lines = f.readlines()[-5:]
                        for line in lines:
                            self.stdout.write(f"   {line.strip()}")
                except Exception as e:
                    self.stdout.write(f"   ❌ Error leyendo log: {str(e)}")
            else:
                self.stdout.write(f"\n📋 {log_file}: No existe")
