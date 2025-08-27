from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Crea perfiles para usuarios que no los tengan'

    def handle(self, *args, **options):
        users_without_profile = []
        
        for user in User.objects.all():
            try:
                profile = user.profile
            except UserProfile.DoesNotExist:
                users_without_profile.append(user)
        
        if users_without_profile:
            self.stdout.write(f'Encontrados {len(users_without_profile)} usuarios sin perfil')
            
            for user in users_without_profile:
                profile = UserProfile.objects.create(user=user)
                self.stdout.write(f'Perfil creado para usuario: {user.username}')
            
            self.stdout.write(
                self.style.SUCCESS(f'Se crearon {len(users_without_profile)} perfiles de usuario')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Todos los usuarios ya tienen perfil')
            )
