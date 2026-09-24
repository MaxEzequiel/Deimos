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
            
            # Crear el check-in (solo entrada)
            checkin = CheckIn.objects.create(
                dni=dni,
                observaciones=observaciones,
                registrado_por=request.user
            )
            messages.success(request, f"¡Bienvenido! Entrada registrada para DNI {dni}")
            return redirect('checkin_success', pk=checkin.pk)
    
    # Últimos 10 ingresos del día
    hoy = timezone.localdate()
    ultimos = CheckIn.objects.filter(fecha=hoy).order_by('-hora_entrada')[:10]
    
    return render(request, 'checkin/checkin_home.html', {
        'form': form,
        'ultimos': ultimos,
    })


@login_required
def checkin_success(request, pk):
    """Confirmación del check-in"""
    checkin = CheckIn.objects.get(pk=pk)
    return render(request, 'checkin/checkin_success.html', {'checkin': checkin})


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