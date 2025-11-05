from django.db import transaction
from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.utils import timezone

from api.ai_service import OpenRouterAIService
from core.models import Test, TestExecution


# Create your views here.
class TestInicial(APIView):
    # Endpoint para iniciar un test conversacional y obtener la primera respuesta
    def post(self, request, test_id):
        # 1. Obtener el test y el usuario
        test = get_object_or_404(Test, pk=test_id)
        user = request.user

        # 2. Iniciar el registro de la ejecución en la BD
        try:
            profile = user.entityprofile
        except AttributeError:
            return Response({
                "error": "Usuario no encontrado",
            }, status=status.HTTP_403_FORBIDDEN)

        # La ejecución se crea solo si la API responde
        with transaction.atomic():
            execution = TestExecution.objects.create(
                test=test,
                user=user,
                entity=profile.entity,
            )

            # 3. Llamamos al servicio de IA
            ai_service = OpenRouterAIService(system_prompt=test.ai_prompt_instructions)

            mensaje_user_inicial = request.data.get("message", "Hola, estoy listo para empezar el test.")
            ai_response_data = ai_service.start_conversacion(mensaje_user_inicial)

            if 'error' in ai_response_data:
                # Si la IA falla, abortamos la transición
                return Response(ai_response_data, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            # 4. Actualizar el chat_log
            mensaje_asistente = ai_response_data["choices"][0]["message"]
            execution.chat_log = [
                {
                    "role": "user",
                    "content": mensaje_user_inicial,
                },
                {
                    "role": "asistente",
                    "content": mensaje_asistente["content"],
                }
            ]
            execution.save()

            return Response({
                "execution_id": execution.id,
                "response": mensaje_asistente["content"],
            }, status=status.HTTP_200_OK)


class TestContinueView(APIView):
    # Endpoint para enviar el siguiente mensaje
    def post(self, request, execution_id):
        execution = get_object_or_404(TestExecution, pk=execution_id, user=request.user)
        mensaje_nuevo_usuario = request.data.get("message")

        if execution.finish_time:
            return Response({
                "error": "Este test ya ha finalizado."
            }, status=status.HTTP_400_BAD_REQUEST)

        if not mensaje_nuevo_usuario:
            return Response({
                "error": "Mensaje de usuario requerido."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 1. Llamar al servicio de IA
        ai_service = OpenRouterAIService()
        ai_response_data = ai_service.continuar_conversacion(execution.chat_log, mensaje_nuevo_usuario)

        if 'error' in ai_response_data:
            return Response(ai_response_data, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 2. Actualizar el chat_log
        mensaje_asistente = ai_response_data["choices"][0]["message"]

        execution.chat_log.append(
            {
                "role": "user",
                "content": mensaje_nuevo_usuario,
            },
            {
                "role": "asistente",
                "content": mensaje_asistente["content"],
            }
        )

        execution.save()

        return Response({
            "response": mensaje_asistente["content"],
        }, status=status.HTTP_200_OK)

class TestFinalView(APIView):
    # Endpoint para marcar un test como finalizado
    def post(self, request, execution_id):
        execution = get_object_or_404(TestExecution, pk=execution_id, user=request.user)

        if execution.finish_time:
            return Response({
                "error": "Este test ya ha finalizado."
            })

        # 1. Marcar como finalizado (para facturación y evitar más mensajes)
        execution.finish_time = timezone.now()

        # 2. Llamada al servicio de evaluación
        test = execution.test
        ai_service = OpenRouterAIService()

        # Usar el chat_log de la ejecución y los criterios del Test
        evaluacion_result = ai_service.evaluar_test(execution.chat_log, test.evaluacion_criteria)

        if 'error' in evaluacion_result:
            # Si falla registramos el fallo y el fin del test
            execution.save()
            return Response(evaluacion_result, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 3. Guardar el resultado y el log
        execution.evaluacion_result = evaluacion_result
        execution.save()

        # TODO lógica para generar el PDF

        return Response({
            "message": "Test finalizado y evaluación completada",
            "evaluation_id": execution.id,
            "results": evaluacion_result,
        }, status=status.HTTP_200_OK)