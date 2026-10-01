from django.contrib.auth.decorators import permission_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect, get_object_or_404
from core.forms import DateRangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import PermissionDenied

from .models import CheckIn
from .forms import CheckInForm
from .services import member_checkin_status


@login_required
@require_http_methods(['GET', 'POST'])
@permission_required("checkin.add_checkin", raise_exception=True)
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
                person=form.person,
                observaciones=observaciones,
                registrado_por=request.user
            )
            messages.success(request, f"¡Bienvenido! Entrada registrada para DNI {dni}")
            return redirect('checkin_success', pk=checkin.pk)
    
    # Últimos 10 ingresos del día
    hoy = timezone.localdate()
    ultimos = CheckIn.objects.select_related('person').filter(fecha=hoy).order_by('-hora_entrada')[:10]
    
    return render(request, 'checkin/checkin_home.html', {
        'form': form,
        'ultimos': ultimos,
    })


@login_required
@require_http_methods(['GET'])
def checkin_success(request, pk):
    """Confirmación del check-in"""
    can_view_all = request.user.has_perm("checkin.view_checkin")
    if not can_view_all and not request.user.has_perm("checkin.add_checkin"):
        raise PermissionDenied
    checkins = CheckIn.objects.select_related('person', 'person__user')
    if not can_view_all:
        checkins = checkins.filter(registrado_por=request.user)
    checkin = get_object_or_404(checkins, pk=pk)
    context = member_checkin_status(checkin.person)
    context['checkin'] = checkin
    return render(request, 'checkin/checkin_success.html', context)


@login_required
@permission_required("checkin.view_checkin", raise_exception=True)
@require_http_methods(['GET'])
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
    
    date_form = DateRangeForm(request.GET)
    if date_form.is_valid():
        if date_form.cleaned_data.get("desde"):
            checkins = checkins.filter(fecha__gte=date_form.cleaned_data["desde"])
        if date_form.cleaned_data.get("hasta"):
            checkins = checkins.filter(fecha__lte=date_form.cleaned_data["hasta"])
    else:
        messages.error(request, "Revisá las fechas del filtro")
        checkins = checkins.none()
    
    hoy = timezone.localdate()
    total_hoy = CheckIn.objects.filter(fecha=hoy).count()
    
    return render(request, 'checkin/checkin_history.html', {
        'checkins': checkins[:200],
        'q': q,
        'desde': desde,
        'hasta': hasta,
        'total_hoy': total_hoy,
    })
