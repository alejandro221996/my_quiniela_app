from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'tipo_usuario', 'apuestas_realizadas', 'promocion_solicitada', 'fecha_promocion']
    list_filter = ['tipo_usuario', 'promocion_solicitada']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['fecha_promocion', 'fecha_solicitud_promocion']
    
    actions = ['promover_a_organizador']
    
    def promover_a_organizador(self, request, queryset):
        count = 0
        for profile in queryset:
            if profile.tipo_usuario == 'PARTICIPANTE':
                profile.promover_a_organizador()
                count += 1
        self.message_user(request, f'{count} usuarios promovidos a Organizador.')
    promover_a_organizador.short_description = "Promover a Organizador"
