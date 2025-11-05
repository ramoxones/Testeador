from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Entity, EntityProfile, Test, TestExecution

# Register your models here.
class EntityProfileInLine(admin.StackedInline):
    # Permite editar el perfil de la entidad junto con el usuario
    model = EntityProfile
    can_delete = False
    verbose_name_plural = "Perfil de Entidad"

class UserAdmin(BaseUserAdmin):
    # Administrador y usuarios para incluir el perfil de entidad
    inlines = (EntityProfileInLine,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_entity')

    @admin.display(description='Entidad Asignada')
    def get_entity(self, obj):
        return obj.entityprofile.entity.name if hasattr(obj, 'entityprofile') else 'N/A'

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email', 'is_active')
    search_fields = ('name', 'contact_email')
    list_filter = ('is_active',)

# Gestión de Test y resultados
@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'purpose')
    search_fields = ('name', 'purpose')
    fields = ('name', 'purpose', 'creator', 'ai_prompt_instructions', 'evaluation_criteria')
    readonly_fields = ('creator',)

    # Asigna automáticamente el usuario logueado como creador
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.creator = request.user
        super().save_model(request, obj, form, change)

@admin.register(TestExecution)
class TestExecutionAdmin(admin.ModelAdmin):
    list_display = ('test', 'user', 'entity', 'start_time', 'finish_time', 'was_successful',)
    list_filter = ('entity', 'test', 'finish_time',)
    search_fields = ('user__username', 'test__name', 'entity__name',)
    readonly_fields = ('test', 'user', 'entity', 'start_time', 'finish_time', 'chat_log', 'evaluation_result',
                       'pdf_report_path')

    @admin.display(description='Completado')
    def was_successful(self, obj):
        return bool(obj.finish_time)
    was_successful.boolean = True