from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from .models import CheckIn
from .forms import CheckInForm


@login_required
def checkin_home(request):
    """Pantalla principal: registrar entrada por DNI"""
    form = CheckInForm()
    
    if request.method == 'POST':
        form = CheckInForm(request.POST)
        if form.is_valid():
            dni = form.cleaned_data['dni'].strip()
            observaciones = form.cleaned_data.get('observaciones', '')
            
            checkin = CheckIn.objects.create(
                dni=dni,
                observaciones=observaciones,
                registrado_por=request.user
            )
            messages.success(request, f"¡Bienvenido! Entrada registrada para DNI {dni}")
            return redirect('checkin_success', pk=checkin.pk)
    
    hoy = timezone.localdate()
    ultimos = CheckIn.objects.filter(fecha=hoy).order_by('-hora_entrada')[:10]
    
    return render(request, 'checkin/checkin_home.html', {
        'form': form,
        'ultimos': ultimos,
    })


@login_required
def checkin_success(request, pk):
    """Confirmación del check-in con estado real de membresía"""
    checkin = CheckIn.objects.get(pk=pk)
    
    membership_info = None
    if checkin.person and checkin.person.user:
        try:
            from memberships.models import Membership
            
            membership = Membership.objects.filter(user=checkin.person.user).first()
            
            if membership:
                hoy = timezone.localdate()
                
                if not membership.start_date or not membership.end_date:
                    membership_info = {
                        'sin_fechas': True,
                        'plan_nombre': membership.plan.name if membership.plan else 'Sin plan',
                        'estado': membership.status,
                    }
                else:
                    dias_restantes = membership.dias_restantes
                    dias_totales = membership.dias_totales
                    dias_transcurridos = membership.dias_transcurridos
                    porcentaje = membership.porcentaje_transcurrido
                    
                    if membership.status != 'active':
                        estado = 'inactiva'
                        color = '#95a5a6'
                        mensaje = 'Membresía inactiva'
                    elif dias_restantes < 0:
                        estado = 'vencida'
                        color = '#e74c3c'
                        mensaje = f'Vencida hace {abs(dias_restantes)} días'
                    elif dias_restantes == 0:
                        estado = 'vence_hoy'
                        color = '#e74c3c'
                        mensaje = 'Vence hoy'
                    elif dias_restantes <= 3:
                        estado = 'por_vencer'
                        color = '#f39c12'
                        mensaje = f'Vence en {dias_restantes} días'
                    elif dias_restantes <= 7:
                        estado = 'proxima'
                        color = '#f1c40f'
                        mensaje = f'Vence en {dias_restantes} días'
                    else:
                        estado = 'activa'
                        color = '#2ecc71'
                        mensaje = f'Activa por {dias_restantes} días más'
                    
                    membership_info = {
                        'sin_fechas': False,
                        'fecha_inicio': membership.start_date,
                        'fecha_vencimiento': membership.end_date,
                        'dias_totales': dias_totales,
                        'dias_transcurridos': max(0, dias_transcurridos),
                        'dias_restantes': dias_restantes,
                        'porcentaje': porcentaje,
                        'estado': estado,
                        'color': color,
                        'mensaje': mensaje,
                        'plan_nombre': membership.plan.name if membership.plan else 'Sin plan',
                    }
        except Exception as e:
            print(f"Error al calcular membresía: {e}")
    
    return render(request, 'checkin/checkin_success.html', {
        'checkin': checkin,
        'membership': membership_info,
    })


@login_required
def checkin_history(request):
    """Historial de ingresos con filtros"""
    q = request.GET.get('q', '').strip()
    desde = request.GET.get('desde', '')
    hasta = request.GET.get('hasta', '')
    
    checkins = CheckIn.objects.select_related('person', 'registrado_por')
    
    if q:
        checkins = checkins.filter(
            Q(dni__icontains=q) |
            Q(person__name__icontains=q) |
            Q(person__surname__icontains=q)
        )
    
    if desde:
        checkins = checkins.filter(fecha__gte=desde)
    if hasta:
        checkins = checkins.filter(fecha__lte=hasta)
    
    hoy = timezone.localdate()
    total_hoy = CheckIn.objects.filter(fecha=hoy).count()
    
    return render(request, 'checkin/checkin_history.html', {
        'checkins': checkins[:200],
        'q': q,
        'desde': desde,
        'hasta': hasta,
        'total_hoy': total_hoy,
    })