from django.db import models
from django.contrib.auth.models import User

class Entity(models.Model):
    # Representa la empresa o cliente que usa la plataforma para facturación
    name = models.CharField(max_length=255, unique=True)
    contact_email = models.EmailField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Entidades'

class EntityProfile(models.Model):
    # Extiende el usuario de Django para asociarlo a entidad y rol
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='users')
    is_manager = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.entity.name}"

    class Meta:
        verbose_name = "Perfil de Entidad"


class Test(models.Model):
    # Define la configuración y las instruccioens del test convencional
    name = models.CharField(max_length=255)
    purpose = models.TextField()

    # PROMPT que dicta como debe actuar el modelo
    ai_prompt_instructions = models.TextField(
        help_text="Prompt base para el modelo"
    )
    evaluation_criteria = models.JSONField(
        help_text="Criterios de evaluación (por ej. competencias) y su descripción"
    )

    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_test')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Test de Conversación"

class TestExecution(models.Model):
    # Registro de cada test completo por un usuario
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    finish_time = models.DateTimeField(null=True, blank=True)

    # Registro de la conversación completa
    chat_log = models.JSONField(default=list)

    # Resultado e Interpretación (JSON devuelto por la IA)
    evaluation_result = models.JSONField(null=True, blank=True)

    pdf_report_path = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Ejecución de {self.test.name} por {self.user.username} ({self.entity.name})"

    class Meta:
        verbose_name = "Ejecución de test"
        ordering = ['-start_time']