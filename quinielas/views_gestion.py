"""
Vistas para gestión de participantes por parte del creador
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from .models import Quiniela, Participante
from decimal import Decimal


@login_required
def gestionar_participantes(request, quiniela_id):
    """Vista para que el creador gestione participantes de su quiniela"""
    quiniela = get_object_or_404(Quiniela, id=quiniela_id, creador=request.user)
    
    # Obtener participantes con filtros
    filtro_estado = request.GET.get('estado', 'TODOS')
    participantes = quiniela.participantes.all()
    
    if filtro_estado != 'TODOS':
        participantes = participantes.filter(estado=filtro_estado)
    
    # Paginación
    paginator = Paginator(participantes, 20)
    page = request.GET.get('page')
    participantes_page = paginator.get_page(page)
    
    # Estadísticas
    stats = {
        'total': quiniela.participantes.count(),
        'pagados': quiniela.participantes.filter(estado='PAGADO').count(),
        'pendientes': quiniela.participantes.filter(estado='PENDIENTE').count(),
        'suspendidos': quiniela.participantes.filter(estado='SUSPENDIDO').count(),
        'total_recaudado': sum(
            p.monto_pagado or 0 
            for p in quiniela.participantes.filter(estado='PAGADO')
        )
    }
    
    context = {
        'quiniela': quiniela,
        'participantes': participantes_page,
        'filtro_estado': filtro_estado,
        'stats': stats,
        'estados_choices': Participante.ESTADOS_PARTICIPANTE,
    }
    
    return render(request, 'quinielas/gestionar_participantes.html', context)


@login_required
def marcar_pago_participante(request, quiniela_id, participante_id):
    """Marca a un participante como pagado"""
    quiniela = get_object_or_404(Quiniela, id=quiniela_id, creador=request.user)
    participante = get_object_or_404(Participante, id=participante_id, quiniela=quiniela)
    
    if request.method == 'POST':
        monto = request.POST.get('monto')
        metodo_pago = request.POST.get('metodo_pago', 'No especificado')
        
        try:
            monto_decimal = Decimal(monto) if monto else quiniela.precio_entrada
            participante.marcar_como_pagado(monto_decimal, metodo_pago, request.user)
            
            messages.success(
                request, 
                f"✅ {participante.usuario.get_full_name() or participante.usuario.username} "
                f"marcado como pagado (${monto_decimal})"
            )
        except ValueError:
            messages.error(request, "❌ Monto inválido")
    
    return redirect('quinielas:gestionar_participantes', quiniela_id=quiniela.id)


@login_required
def cambiar_estado_participante(request, quiniela_id, participante_id):
    """Cambia el estado de un participante"""
    quiniela = get_object_or_404(Quiniela, id=quiniela_id, creador=request.user)
    participante = get_object_or_404(Participante, id=participante_id, quiniela=quiniela)
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        razon = request.POST.get('razon', '')
        
        if nuevo_estado in ['PENDIENTE', 'PAGADO', 'SUSPENDIDO', 'ELIMINADO']:
            estado_anterior = participante.get_estado_display()
            
            if nuevo_estado == 'SUSPENDIDO':
                participante.suspender(razon, request.user)
            elif nuevo_estado == 'PAGADO':
                # Reactivar si tenía pago previo
                participante.reactivar(request.user)
            else:
                participante.estado = nuevo_estado
                if razon:
                    participante.notas_admin = razon
                participante.actualizado_por = request.user
                participante.save()
            
            messages.success(
                request,
                f"✅ Estado de {participante.usuario.username} cambiado de "
                f"{estado_anterior} a {participante.get_estado_display()}"
            )
        else:
            messages.error(request, "❌ Estado inválido")
    
    return redirect('quinielas:gestionar_participantes', quiniela_id=quiniela.id)


@login_required
def eliminar_participante(request, quiniela_id, participante_id):
    """Elimina un participante de la quiniela"""
    quiniela = get_object_or_404(Quiniela, id=quiniela_id, creador=request.user)
    participante = get_object_or_404(Participante, id=participante_id, quiniela=quiniela)
    
    if request.method == 'POST':
        usuario_nombre = participante.usuario.get_full_name() or participante.usuario.username
        
        # Eliminar apuestas asociadas primero
        participante.apuestas.all().delete()
        
        # Eliminar participante
        participante.delete()
        
        messages.success(
            request,
            f"✅ {usuario_nombre} ha sido eliminado de la quiniela"
        )
    
    return redirect('quinielas:gestionar_participantes', quiniela_id=quiniela.id)


@login_required
def exportar_participantes(request, quiniela_id):
    """Exporta lista de participantes en formato CSV"""
    import csv
    from django.http import HttpResponse
    
    quiniela = get_object_or_404(Quiniela, id=quiniela_id, creador=request.user)
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="participantes_{quiniela.nombre}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Usuario', 'Nombre Completo', 'Email', 'Estado', 'Fecha Unión', 
        'Fecha Pago', 'Monto Pagado', 'Método Pago', 'Puntos', 'Notas'
    ])
    
    for p in quiniela.participantes.all():
        writer.writerow([
            p.usuario.username,
            p.usuario.get_full_name(),
            p.usuario.email,
            p.get_estado_display(),
            p.fecha_union.strftime('%Y-%m-%d'),
            p.fecha_pago.strftime('%Y-%m-%d') if p.fecha_pago else '',
            p.monto_pagado or '',
            p.metodo_pago,
            p.puntos_totales,
            p.notas_admin
        ])
    
    return response


@login_required
def dashboard_creador(request, quiniela_id):
    """Dashboard específico para el creador de la quiniela"""
    quiniela = get_object_or_404(Quiniela, id=quiniela_id, creador=request.user)
    
    # Estadísticas financieras y de participación
    participantes = quiniela.participantes.all()
    participantes_pagados = participantes.filter(estado='PAGADO')
    participantes_pendientes = participantes.filter(estado='PENDIENTE')
    participantes_suspendidos = participantes.filter(estado='SUSPENDIDO')
    
    total_recaudado = sum(p.monto_pagado or 0 for p in participantes_pagados)
    
    # Top participantes por puntos
    top_participantes = participantes.order_by('-puntos_totales')[:5]
    
    # Actividad reciente (últimos movimientos)
    actividad_reciente = []
    
    # Últimos pagos
    for p in participantes_pagados.filter(fecha_pago__isnull=False).order_by('-fecha_pago')[:3]:
        actividad_reciente.append({
            'tipo': 'pago',
            'descripcion': f'{p.usuario.get_full_name() or p.usuario.username} realizó pago de ${p.monto_pagado}',
            'fecha': p.fecha_pago
        })
    
    # Últimas uniones
    for p in participantes.order_by('-fecha_union')[:3]:
        actividad_reciente.append({
            'tipo': 'union',
            'descripcion': f'{p.usuario.get_full_name() or p.usuario.username} se unió a la quiniela',
            'fecha': p.fecha_union
        })
    
    # Ordenar por fecha
    actividad_reciente.sort(key=lambda x: x['fecha'], reverse=True)
    actividad_reciente = actividad_reciente[:5]
    
    # Recordatorios para el creador
    recordatorios = []
    if participantes_pendientes.count() > 0:
        recordatorios.append(f"Hay {participantes_pendientes.count()} participantes con pagos pendientes")
    if participantes_suspendidos.count() > 0:
        recordatorios.append(f"Hay {participantes_suspendidos.count()} participantes suspendidos")
    
    # Calcular porcentaje de pagos
    total_participantes = participantes.count()
    porcentaje_pagado = (participantes_pagados.count() / total_participantes * 100) if total_participantes > 0 else 0
    
    # Stats para el template
    stats = {
        'total_participantes': total_participantes,
        'pagos_recibidos': participantes_pagados.count(),
        'pagos_pendientes': participantes_pendientes.count(),
        'total_recaudado': total_recaudado,
        'total': total_participantes,
        'pagados': participantes_pagados.count(),
        'pendientes': participantes_pendientes.count(),
        'suspendidos': participantes_suspendidos.count(),
        'porcentaje_pagado': round(porcentaje_pagado, 1),
        'total_partidos': 10,  # Placeholder, ajustar según tu modelo
        'total_apuestas': sum(p.total_apuestas for p in participantes)
    }
    
    context = {
        'quiniela': quiniela,
        'stats': stats,
        'top_participantes': top_participantes,
        'actividad_reciente': actividad_reciente,
        'recordatorios': recordatorios,
    }
    
    return render(request, 'quinielas/dashboard_creador.html', context)
