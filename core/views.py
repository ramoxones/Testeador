from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseForbidden
from .models import Entity, EntityProfile, TestExecution


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Credenciales inválidas. Inténtalo de nuevo.')

    return render(request, 'core/login.html')


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        email = (request.POST.get('email') or '').strip()
        password = (request.POST.get('password') or '').strip()

        if not username or not password:
            messages.error(request, 'Usuario y contraseña son obligatorios.')
            return render(request, 'core/register.html')

        # Evitar duplicados de nombre de usuario sin distinguir mayúsculas/minúsculas
        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, 'El nombre de usuario ya existe. Por favor, elige otro nombre.')
            return render(request, 'core/register.html')

        user = User.objects.create_user(username=username, email=email, password=password)

        # Asignar a una entidad por defecto
        default_entity, _ = Entity.objects.get_or_create(
            name='Default',
            defaults={'contact_email': email or 'default@example.com', 'is_active': True}
        )
        EntityProfile.objects.create(user=user, entity=default_entity, is_manager=False)

        login(request, user)
        return redirect('dashboard')

    return render(request, 'core/register.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    return render(request, 'core/dashboard.html', {})


@require_http_methods(["GET"])
@login_required
def export_tests_by_user_html(request):
    # Solo personal con permisos
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponseForbidden("No autorizado")

    username = (request.GET.get('username') or '').strip()
    if not username:
        return render(request, 'core/export_user_tests.html', {
            'error': "Parámetro 'username' requerido",
            'username': None,
            'executions': [],
            'count': 0,
        })

    user = User.objects.filter(username=username).first()
    if not user:
        return render(request, 'core/export_user_tests.html', {
            'error': "Usuario no encontrado",
            'username': username,
            'executions': [],
            'count': 0,
        })

    executions = TestExecution.objects.filter(user=user).order_by('-start_time')
    return render(request, 'core/export_user_tests.html', {
        'error': None,
        'username': username,
        'executions': executions,
        'count': executions.count(),
    })
