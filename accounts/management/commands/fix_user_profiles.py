from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Verifica y repara perfiles de usuarios faltantes o corruptos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo mostrar qué se haría sin hacer cambios reales',
        )
        parser.add_argument(
            '--fix-all',
            action='store_true',
            help='Reparar todos los problemas encontrados automáticamente',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Verificar solo un usuario específico',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fix_all = options['fix_all']
        specific_user = options.get('username')

        self.stdout.write(
            self.style.SUCCESS('🔍 Iniciando verificación de perfiles de usuarios...\n')
        )

        # Obtener usuarios a verificar
        if specific_user:
            try:
                users = User.objects.filter(username=specific_user)
                if not users.exists():
                    self.stdout.write(
                        self.style.ERROR(f'❌ Usuario "{specific_user}" no encontrado')
                    )
                    return
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error buscando usuario: {str(e)}')
                )
                return
        else:
            users = User.objects.all()

        # Contadores
        users_checked = 0
        profiles_missing = 0
        profiles_fixed = 0
        profiles_corrupted = 0
        errors = 0

        for user in users:
            users_checked += 1
            try:
                # Verificar si tiene perfil
                if not hasattr(user, 'profile'):
                    profiles_missing += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️  Usuario {user.username} (ID: {user.id}) no tiene perfil'
                        )
                    )

                    if fix_all and not dry_run:
                        # Crear perfil faltante
                        with transaction.atomic():
                            profile = UserProfile.objects.create(
                                user=user,
                                tipo_usuario='PARTICIPANTE'
                            )
                            profiles_fixed += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'✅ Perfil creado para {user.username} (ID: {profile.id})'
                                )
                            )
                    elif dry_run:
                        self.stdout.write(
                            self.style.NOTICE(
                                f'🔧 [DRY RUN] Se crearía perfil para {user.username}'
                            )
                        )

                else:
                    # Verificar integridad del perfil existente
                    profile = user.profile
                    corrupted_fields = []

                    # Verificar tipo_usuario
                    if profile.tipo_usuario not in ['PARTICIPANTE', 'ORGANIZADOR']:
                        corrupted_fields.append('tipo_usuario')

                    # Verificar campos numéricos
                    if profile.apuestas_realizadas < 0:
                        corrupted_fields.append('apuestas_realizadas')

                    if corrupted_fields:
                        profiles_corrupted += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f'💥 Perfil corrupto para {user.username}: {corrupted_fields}'
                            )
                        )

                        if fix_all and not dry_run:
                            # Reparar campos corruptos
                            with transaction.atomic():
                                if 'tipo_usuario' in corrupted_fields:
                                    profile.tipo_usuario = 'PARTICIPANTE'
                                if 'apuestas_realizadas' in corrupted_fields:
                                    profile.apuestas_realizadas = 0

                                profile.save()
                                profiles_fixed += 1
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'✅ Perfil reparado para {user.username}'
                                    )
                                )
                        elif dry_run:
                            self.stdout.write(
                                self.style.NOTICE(
                                    f'🔧 [DRY RUN] Se repararía perfil de {user.username}'
                                )
                            )

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Error verificando usuario {user.username}: {str(e)}'
                    )
                )
                logger.error(f'Error en fix_user_profiles para {user.username}: {str(e)}')

        # Reporte final
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📊 REPORTE FINAL'))
        self.stdout.write('='*60)
        self.stdout.write(f'👥 Usuarios verificados: {users_checked}')
        self.stdout.write(f'❌ Perfiles faltantes: {profiles_missing}')
        self.stdout.write(f'💥 Perfiles corruptos: {profiles_corrupted}')
        self.stdout.write(f'✅ Perfiles reparados: {profiles_fixed}')
        self.stdout.write(f'🚨 Errores: {errors}')

        if dry_run:
            self.stdout.write('\n' + self.style.NOTICE('🔍 Modo DRY RUN - No se realizaron cambios'))
            self.stdout.write(
                self.style.NOTICE('Para aplicar las reparaciones, ejecuta: --fix-all')
            )

        if profiles_missing > 0 or profiles_corrupted > 0:
            if not fix_all:
                self.stdout.write('\n' + self.style.WARNING('⚠️  Se encontraron problemas.'))
                self.stdout.write(
                    self.style.WARNING('Ejecuta con --fix-all para repararlos automáticamente')
                )
            else:
                self.stdout.write('\n' + self.style.SUCCESS('🎉 ¡Reparaciones completadas!'))
        else:
            self.stdout.write('\n' + self.style.SUCCESS('🎉 ¡Todos los perfiles están OK!'))
