from django.urls import path
from .views import login_view, register_view, logout_view, dashboard, export_tests_by_user_html

urlpatterns = [
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('', dashboard, name='dashboard'),
    path('export/tests/by_user/', export_tests_by_user_html, name='export-tests-by-user-html'),
]