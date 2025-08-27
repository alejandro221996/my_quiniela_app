#!/usr/bin/env python3
"""
GitHub Automation Script para My Quiniela App
Uso simple: python github_automation.py [comando] [argumentos]

Ejemplos:
    python github_automation.py create-pr "Add match predictions" "feat/predictions"
    python github_automation.py push-files "Update quiniela models"
    python github_automation.py create-branch "feature/user-dashboard"
    python github_automation.py list-repos
"""

import os
import sys
import json
import requests
import subprocess
from pathlib import Path
from datetime import datetime

# Función para cargar variables del .env
def load_env_vars():
    """Cargar variables de entorno desde archivo .env"""
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Cargar variables de entorno
load_env_vars()

# Configuración
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
if not GITHUB_TOKEN:
    print("❌ Error: GITHUB_TOKEN no encontrado")
    print("ℹ️  Opciones para configurarlo:")
    print("   1. Ejecuta: python3 setup_env.py")
    print("   2. Crea archivo .env con: GITHUB_TOKEN=tu_token")
    print("   3. Exporta variable: export GITHUB_TOKEN=tu_token")
    sys.exit(1)

GITHUB_OWNER = os.environ.get('GITHUB_OWNER', 'alejandro221996')
GITHUB_REPO = os.environ.get('GITHUB_REPO', 'my_quiniela_app')

class GitHubAutomation:
    def __init__(self):
        self.token = GITHUB_TOKEN
        self.owner = GITHUB_OWNER
        self.repo = GITHUB_REPO
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        self.base_url = f'https://api.github.com/repos/{self.owner}/{self.repo}'

    def print_success(self, msg):
        print(f"✅ {msg}")

    def print_error(self, msg):
        print(f"❌ {msg}")

    def print_info(self, msg):
        print(f"ℹ️  {msg}")

    def run_git_command(self, command):
        """Ejecutar comando git local"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                self.print_error(f"Git error: {result.stderr}")
                return None
        except Exception as e:
            self.print_error(f"Error executing git command: {e}")
            return None

    def create_branch(self, branch_name):
        """Crear nueva rama"""
        print(f"🌿 Creando rama: {branch_name}")

        # Obtener SHA del branch principal
        response = requests.get(f"{self.base_url}/git/refs/heads/main", headers=self.headers)
        if response.status_code != 200:
            self.print_error(f"No se pudo obtener referencia main: {response.text}")
            return False

        main_sha = response.json()['object']['sha']

        # Crear nueva rama
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": main_sha
        }

        response = requests.post(f"{self.base_url}/git/refs", headers=self.headers, json=data)
        if response.status_code == 201:
            self.print_success(f"Rama '{branch_name}' creada exitosamente")

            # Cambiar a la nueva rama localmente
            self.run_git_command(f"git checkout -b {branch_name}")
            return True
        else:
            self.print_error(f"Error creando rama: {response.text}")
            return False

    def push_files(self, commit_message, branch="main"):
        """Push de archivos modificados"""
        print(f"📤 Subiendo cambios con mensaje: '{commit_message}'")

        # Comandos git locales
        commands = [
            "git add .",
            f'git commit -m "{commit_message}"',
            f"git push origin {branch}"
        ]

        for cmd in commands:
            self.print_info(f"Ejecutando: {cmd}")
            result = self.run_git_command(cmd)
            if result is None:
                return False

        self.print_success("Archivos subidos exitosamente")
        return True

    def create_pull_request(self, title, branch, base="main", body=""):
        """Crear Pull Request"""
        print(f"🔄 Creando PR: '{title}'")

        if not body:
            body = f"""## 📋 Descripción
{title}

## ⚽ Funcionalidades de Quinielas
- [ ] Sistema de predicciones
- [ ] Gestión de usuarios
- [ ] Cálculo de puntuaciones
- [ ] Dashboard de resultados

## 🎯 Tipo de cambio
- [ ] ✨ Nueva funcionalidad
- [ ] 🐛 Bug fix
- [ ] 📚 Documentación
- [ ] 🎨 Refactoring
- [ ] ⚡ Mejora de rendimiento

## 🧪 Testing
- [ ] Tests unitarios ejecutados localmente
- [ ] Tests de integración ejecutados
- [ ] Revisión manual realizada
- [ ] Tests de predicciones verificados

## 📱 Áreas de Quinielas Afectadas
- [ ] Modelos de datos (partidos, equipos, predicciones)
- [ ] Sistema de autenticación
- [ ] API de predicciones
- [ ] Frontend/UI
- [ ] Cálculo de puntuaciones
- [ ] Dashboard de usuarios

## 📝 Notas para el revisor
Cambios realizados en el sistema de quinielas.

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        data = {
            "title": title,
            "body": body,
            "head": branch,
            "base": base
        }

        response = requests.post(f"{self.base_url}/pulls", headers=self.headers, json=data)
        if response.status_code == 201:
            pr_url = response.json()['html_url']
            pr_number = response.json()['number']
            self.print_success(f"PR #{pr_number} creado: {pr_url}")
            return pr_url
        else:
            self.print_error(f"Error creando PR: {response.text}")
            return None

    def list_repos(self):
        """Listar repositorios del usuario"""
        print("📋 Repositorios disponibles:")

        response = requests.get(f"https://api.github.com/user/repos", headers=self.headers)
        if response.status_code == 200:
            repos = response.json()
            for repo in repos[:10]:  # Mostrar solo los primeros 10
                private = "🔒" if repo['private'] else "🌍"
                print(f"  {private} {repo['full_name']} - {repo.get('description', 'Sin descripción')}")
        else:
            self.print_error(f"Error listando repos: {response.text}")

    def get_repo_info(self):
        """Obtener información del repositorio actual"""
        print(f"📊 Información del repositorio: {self.owner}/{self.repo}")

        response = requests.get(self.base_url, headers=self.headers)
        if response.status_code == 200:
            repo = response.json()
            print(f"  📝 Descripción: {repo.get('description', 'App de Quinielas Django')}")
            print(f"  🌟 Stars: {repo['stargazers_count']}")
            print(f"  🍴 Forks: {repo['forks_count']}")
            print(f"  🔀 Branches: {len(self.list_branches())}")
            print(f"  📂 Tamaño: {repo['size']} KB")
            print(f"  🔒 Privado: {'Sí' if repo['private'] else 'No'}")
            print(f"  ⚽ Proyecto: Sistema de Quinielas Django")
        else:
            self.print_error(f"Error obteniendo info del repo: {response.text}")

    def list_branches(self):
        """Listar ramas del repositorio"""
        response = requests.get(f"{self.base_url}/branches", headers=self.headers)
        if response.status_code == 200:
            branches = response.json()
            branch_names = [branch['name'] for branch in branches]
            print(f"🌿 Ramas disponibles ({len(branch_names)}):")
            for branch in branch_names:
                print(f"  - {branch}")
            return branch_names
        else:
            self.print_error(f"Error listando ramas: {response.text}")
            return []

    def quick_commit_and_pr(self, feature_name, description=""):
        """Flujo completo: crear rama, commit, push y PR"""
        print(f"🚀 Flujo completo para: {feature_name}")

        # Nombre de rama amigable para quinielas
        branch_name = f"feature/{feature_name.lower().replace(' ', '-').replace('_', '-')}"

        # 1. Crear rama
        if not self.create_branch(branch_name):
            return False

        # 2. Push archivos
        commit_msg = f"feat: {feature_name}"
        if not self.push_files(commit_msg, branch_name):
            return False

        # 3. Crear PR
        pr_title = f"⚽ [Quinielas] {feature_name}"
        pr_body = description if description else f"Implementación de {feature_name} en el sistema de quinielas"

        pr_url = self.create_pull_request(pr_title, branch_name, body=pr_body)
        if pr_url:
            self.print_success(f"🎉 Flujo completado! PR creado: {pr_url}")
            return True

        return False

    def django_utils(self, action):
        """Utilidades específicas de Django para quinielas"""
        if action == "migrate":
            print("🔄 Ejecutando migraciones de Django...")
            result = self.run_git_command("python manage.py migrate")
            if result is not None:
                self.print_success("Migraciones ejecutadas correctamente")

        elif action == "makemigrations":
            print("📝 Creando migraciones de Django...")
            result = self.run_git_command("python manage.py makemigrations")
            if result is not None:
                self.print_success("Migraciones creadas correctamente")

        elif action == "collectstatic":
            print("📦 Recolectando archivos estáticos...")
            result = self.run_git_command("python manage.py collectstatic --noinput")
            if result is not None:
                self.print_success("Archivos estáticos recolectados")

        elif action == "test":
            print("🧪 Ejecutando tests de Django...")
            result = self.run_git_command("python manage.py test")
            if result is not None:
                self.print_success("Tests ejecutados correctamente")

def show_help():
    """Mostrar ayuda"""
    print("""
⚽ GitHub Automation para My Quiniela App
========================================

Comandos disponibles:

📋 Información:
  info                          - Información del repositorio
  repos                         - Listar repositorios
  branches                      - Listar ramas

🌿 Gestión de ramas:
  create-branch <nombre>        - Crear nueva rama

📤 Commits y Push:
  push "<mensaje>"              - Add, commit y push
  push "<mensaje>" <rama>       - Push a rama específica

🔄 Pull Requests:
  create-pr "<título>" <rama>   - Crear PR
  create-pr "<título>" <rama> "<descripción>" - PR con descripción

🚀 Flujo completo:
  quick "<feature>"             - Rama + commit + push + PR
  quick "<feature>" "<desc>"    - Con descripción personalizada

⚙️  Django Utils:
  django migrate                - Ejecutar migraciones
  django makemigrations         - Crear migraciones
  django collectstatic          - Recolectar archivos estáticos
  django test                   - Ejecutar tests

📖 Ejemplos específicos para Quinielas:
  python github_automation.py quick "match prediction system" "Sistema para predecir resultados de partidos"
  python github_automation.py push "Add quiniela models for matches and teams"
  python github_automation.py create-branch "feature/user-scoring-system"
  python github_automation.py create-pr "Add user dashboard" "feature/dashboard" "Dashboard para ver predicciones"
  python github_automation.py django migrate
""")

def main():
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1].lower()
    gh = GitHubAutomation()

    try:
        if command == "help" or command == "--help" or command == "-h":
            show_help()

        elif command == "info":
            gh.get_repo_info()

        elif command == "repos":
            gh.list_repos()

        elif command == "branches":
            gh.list_branches()

        elif command == "create-branch":
            if len(sys.argv) < 3:
                gh.print_error("Uso: python github_automation.py create-branch <nombre-rama>")
                return
            branch_name = sys.argv[2]
            gh.create_branch(branch_name)

        elif command == "push":
            if len(sys.argv) < 3:
                gh.print_error("Uso: python github_automation.py push \"<mensaje>\" [rama]")
                return
            commit_message = sys.argv[2]
            branch = sys.argv[3] if len(sys.argv) > 3 else "main"
            gh.push_files(commit_message, branch)

        elif command == "create-pr":
            if len(sys.argv) < 4:
                gh.print_error("Uso: python github_automation.py create-pr \"<título>\" <rama> [\"descripción\"]")
                return
            title = sys.argv[2]
            branch = sys.argv[3]
            body = sys.argv[4] if len(sys.argv) > 4 else ""
            gh.create_pull_request(title, branch, body=body)

        elif command == "quick":
            if len(sys.argv) < 3:
                gh.print_error("Uso: python github_automation.py quick \"<feature-name>\" [\"descripción\"]")
                return
            feature_name = sys.argv[2]
            description = sys.argv[3] if len(sys.argv) > 3 else ""
            gh.quick_commit_and_pr(feature_name, description)

        elif command == "django":
            if len(sys.argv) < 3:
                gh.print_error("Uso: python github_automation.py django <migrate|makemigrations|collectstatic|test>")
                return
            action = sys.argv[2]
            gh.django_utils(action)

        else:
            gh.print_error(f"Comando desconocido: {command}")
            show_help()

    except KeyboardInterrupt:
        gh.print_info("Operación cancelada por el usuario")
    except Exception as e:
        gh.print_error(f"Error inesperado: {e}")

if __name__ == "__main__":
    main()
