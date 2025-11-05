from django.urls import path
from .views import TestInicial, TestContinueView, TestFinalView

urlpatterns = [
    # POST /api/test/1/initiate/ --> Inicia el test con ID 1
    path('test/<int:test_id>/initiate/', TestInicial.as_view(), name='test-initiate'),

    # POST /api/test/42/continue/ --> Continua el test con ID de Ejecución 42
    path('test/<int:execution_id>/continue/', TestContinueView.as_view(), name='test-continue'),

    # POST /api/test/42/finish/ --> Finaliza el test con ID de Ejecución 42 y evalúa
    path('test/<int:execution_id>/finish/', TestFinalView.as_view(), name='test-finish'),
]