from django.urls import path
from .views import (
    TestInicial,
    TestContinueView,
    TestFinalView,
    RandomTestView,
    TestLogView,
    CreateTestView,
    CreateCustomTestView,
    ExportTestsByUserView,
    ListTestsView,
    DeleteTestView,
)

urlpatterns = [
    # POST /api/test/1/initiate/ --> Inicia el test con ID 1
    path('test/<int:test_id>/initiate/', TestInicial.as_view(), name='test-initiate'),

    # POST /api/test/42/continue/ --> Continua el test con ID de Ejecución 42
    path('test/<int:execution_id>/continue/', TestContinueView.as_view(), name='test-continue'),

    # POST /api/test/42/finish/ --> Finaliza el test con ID de Ejecución 42 y evalúa
    path('test/<int:execution_id>/finish/', TestFinalView.as_view(), name='test-finish'),
    # GET /api/tests/random/ --> Devuelve un test aleatorio
    path('tests/random/', RandomTestView.as_view(), name='tests-random'),
    # GET /api/test/42/log/ --> Devuelve el chat_log y evaluación
    path('test/<int:execution_id>/log/', TestLogView.as_view(), name='test-log'),
    # POST /api/tests/create/ --> Crea un test (solo admin)
    path('tests/create/', CreateTestView.as_view(), name='tests-create'),
    # POST /api/tests/create_custom/ --> Crea un test personalizado (solo admin)
    path('tests/create_custom/', CreateCustomTestView.as_view(), name='tests-create-custom'),
    # GET /api/tests/export_by_user/?username=<user> --> Exporta ejecuciones de ese usuario (solo admin)
    path('tests/export_by_user/', ExportTestsByUserView.as_view(), name='tests-export-by-user'),
    # GET /api/tests/list/ --> Lista tests (solo admin)
    path('tests/list/', ListTestsView.as_view(), name='tests-list'),
    # DELETE /api/tests/<id>/delete/ --> Elimina un test (solo admin)
    path('tests/<int:test_id>/delete/', DeleteTestView.as_view(), name='tests-delete'),
]