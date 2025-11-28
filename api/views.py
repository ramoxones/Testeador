from django.db import transaction
from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.utils import timezone

from api.ai_service import OpenRouterAIService
from core.models import Test, TestExecution
from django.contrib.auth.models import User
from django.db.models import Count


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

            message_user_initial = request.data.get("message", "Hola, estoy listo para empezar el test.")
            ai_response_data = ai_service.start_conversacion(message_user_initial)

            if 'error' in ai_response_data:
                # Si la IA falla, abortamos la transición
                return Response(ai_response_data, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            # 4. Actualizar el chat_log
            message_assistant = ai_response_data["choices"][0]["message"]
            execution.chat_log = [
                {
                    "role": "user",
                    "content": message_user_initial,
                },
                {
                    "role": "assistant",
                    "content": message_assistant["content"],
                }
            ]
            execution.save()

            return Response({
                "execution_id": execution.id,
                "response": message_assistant["content"],
            }, status=status.HTTP_200_OK)


class TestContinueView(APIView):
    # Endpoint para enviar el siguiente message
    def post(self, request, execution_id):
        execution = get_object_or_404(TestExecution, pk=execution_id, user=request.user)
        message_nuevo_usuario = request.data.get("message")

        if execution.finish_time:
            return Response({
                "error": "Este test ya ha finalizado."
            }, status=status.HTTP_400_BAD_REQUEST)

        if not message_nuevo_usuario:
            return Response({
                "error": "message de usuario requerido."
            }, status=status.HTTP_400_BAD_REQUEST)

        # 1. Llamar al servicio de IA (incluyendo el prompt del sistema del Test)
        ai_service = OpenRouterAIService(system_prompt=execution.test.ai_prompt_instructions)
        ai_response_data = ai_service.continuar_conversacion(execution.chat_log, message_nuevo_usuario)

        if 'error' in ai_response_data:
            return Response(ai_response_data, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 2. Actualizar el chat_log
        message_assistant = ai_response_data["choices"][0]["message"]

        execution.chat_log.append(
            {
                "role": "user",
                "content": message_nuevo_usuario,
            }
        )

        execution.chat_log.append(
            {
                "role": "assistant",
                "content": message_assistant["content"],
            }
        )

        execution.save()

        return Response({
            "response": message_assistant["content"],
        }, status=status.HTTP_200_OK)

class TestFinalView(APIView):
    # Endpoint para marcar un test como finalizado
    def post(self, request, execution_id):
        execution = get_object_or_404(TestExecution, pk=execution_id, user=request.user)

        if execution.finish_time:
            return Response({
                "error": "Este test ya ha finalizado."
            })

        # 1. Marcar como finalizado (para facturación y evitar más messages)
        execution.finish_time = timezone.now()

        # 2. Llamada al servicio de evaluación
        test = execution.test
        ai_service = OpenRouterAIService()

        # Usar el chat_log de la ejecución y los criterios del Test
        evaluation_result = ai_service.evaluar_test(execution.chat_log, test.evaluation_criteria)

        if 'error' in evaluation_result:
            # Si falla, guardar el detalle del error en evaluation_result para trazabilidad
            execution.evaluation_result = evaluation_result
            execution.save()
            return Response(evaluation_result, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 3. Guardar el resultado y el log
        execution.evaluation_result = evaluation_result
        execution.save()

        # TODO lógica para generar el PDF

        return Response({
            "message": "Test finalizado y evaluación completada",
            "evaluation_id": execution.id,
            "results": evaluation_result,
        }, status=status.HTTP_200_OK)


class RandomTestView(APIView):
    # Devuelve un test aleatorio disponible para iniciar
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "No autenticado"}, status=status.HTTP_403_FORBIDDEN)
        test = Test.objects.order_by('?').first()
        if not test:
            # Crear un test de ejemplo para facilitar pruebas
            test = Test.objects.create(
                name='Test de Ejemplo',
                purpose='Prueba rápida del flujo conversacional',
                ai_prompt_instructions=(
                    'Eres un entrevistador. Haz 3 preguntas claras, una a la vez. '
                    'Evalúa comunicación, resolución de problemas y trabajo en equipo.'
                ),
                evaluation_criteria={
                    "comunicacion": "Claridad expresando ideas y escuchando.",
                    "resolucion_problemas": "Capacidad para analizar y proponer soluciones.",
                    "trabajo_equipo": "Colaboración y respeto por otros." 
                },
                creator=request.user
            )
        return Response({
            "test_id": test.id,
            "name": test.name,
            "purpose": test.purpose,
        })


class TestLogView(APIView):
    # Devuelve el chat_log y evaluación (si existe) para descarga
    def get(self, request, execution_id):
        if not request.user.is_authenticated:
            return Response({"error": "No autenticado"}, status=status.HTTP_403_FORBIDDEN)
        execution = get_object_or_404(TestExecution, pk=execution_id, user=request.user)
        return Response({
            "execution_id": execution.id,
            "test": execution.test.name,
            "chat_log": execution.chat_log,
            "evaluation_result": execution.evaluation_result,
            "start_time": execution.start_time,
            "finish_time": execution.finish_time,
        })


class CreateTestView(APIView):
    # Crea un test basado en plantillas predefinidas (solo admin)
    def post(self, request):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        template_key = request.data.get('template')
        TEMPLATES = {
            "entrevista_tecnica": {
                "name": "Entrevista Técnica",
                "purpose": "Evaluar conocimientos técnicos básicos.",
                "ai_prompt_instructions": (
                    "Eres un entrevistador técnico. Realiza 5 preguntas técnicas sencillas, una a la vez, "
                    "sobre programación, estructuras de datos y debugging. Guía la conversación y profundiza si hace falta."
                ),
                "evaluation_criteria": {
                    "conocimiento_tecnico": "Dominio de conceptos básicos y su aplicación.",
                    "razonamiento": "Capacidad para explicar y razonar soluciones.",
                    "claridad": "Comunicación clara y ordenada."
                }
            },
            "soft_skills": {
                "name": "Evaluación Soft Skills",
                "purpose": "Evaluar habilidades blandas en un contexto laboral.",
                "ai_prompt_instructions": (
                    "Actúa como evaluador de soft skills. Haz 4 preguntas sobre comunicación, trabajo en equipo, "
                    "gestión de conflictos y liderazgo. Mantén un tono profesional y empático."
                ),
                "evaluation_criteria": {
                    "comunicacion": "Claridad y escucha activa.",
                    "trabajo_equipo": "Colaboración y responsabilidad compartida.",
                    "gestion_conflictos": "Manejo de desacuerdos y búsqueda de consenso.",
                    "liderazgo": "Iniciativa e influencia positiva."
                }
            },
            "idiomas": {
                "name": "Evaluación de Idiomas",
                "purpose": "Medir competencia comunicativa en idioma extranjero.",
                "ai_prompt_instructions": (
                    "Eres un examinador de idiomas. Conversa en inglés (nivel B2), realiza 5 preguntas, "
                    "corrige errores suavemente y evalúa fluidez, gramática y vocabulario."
                ),
                "evaluation_criteria": {
                    "fluency": "Fluidez y ritmo natural.",
                    "grammar": "Uso correcto de estructuras gramaticales.",
                    "vocabulary": "Variedad y precisión del vocabulario."
                }
            },
        }

        if template_key not in TEMPLATES:
            return Response({"error": "Plantilla no válida"}, status=status.HTTP_400_BAD_REQUEST)

        tpl = TEMPLATES[template_key]
        test = Test.objects.create(
            name=tpl["name"],
            purpose=tpl["purpose"],
            ai_prompt_instructions=tpl["ai_prompt_instructions"],
            evaluation_criteria=tpl["evaluation_criteria"],
            creator=request.user,
        )

        return Response({
            "message": "Test creado",
            "test_id": test.id,
            "name": test.name,
        }, status=status.HTTP_201_CREATED)


class CreateCustomTestView(APIView):
    # Crea un test personalizado por 'tema' o por 'preguntas' (solo admin)
    def post(self, request):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        mode = (request.data.get('mode') or '').strip()
        if mode not in {'tema', 'preguntas'}:
            return Response({"error": "Modo inválido. Usa 'tema' o 'preguntas'"}, status=status.HTTP_400_BAD_REQUEST)

        if mode == 'tema':
            topic = (request.data.get('topic') or '').strip()
            if not topic:
                return Response({"error": "El campo 'topic' es obligatorio"}, status=status.HTTP_400_BAD_REQUEST)
            # Número de preguntas deseado (por defecto 5, rango 1..50)
            try:
                count = int(request.data.get('count') or 5)
            except (TypeError, ValueError):
                count = 5
            count = max(1, min(count, 50))

            name = f"Test: {topic}"
            purpose = f"Evaluación conversacional sobre el tema: {topic}"
            ai_prompt = (
                "Eres un entrevistador experto en el tema indicado. "
                f"Haz {count} preguntas, una a la vez, "
                "profundizando en el tema cuando sea necesario. Sé claro y guía la conversación. "
                f"Tema: {topic}."
            )
            criteria = {
                "conocimiento": "Dominio del tema y conceptos clave.",
                "razonamiento": "Capacidad de explicar y argumentar.",
                "comunicacion": "Claridad y coherencia en las respuestas."
            }

        else:  # mode == 'preguntas'
            questions = request.data.get('questions')
            if not isinstance(questions, list) or not questions:
                return Response({"error": "'questions' debe ser una lista con al menos una pregunta"}, status=status.HTTP_400_BAD_REQUEST)

            # Limpiar preguntas
            cleaned = [str(q).strip() for q in questions if str(q).strip()]
            if not cleaned:
                return Response({"error": "La lista de preguntas no puede quedar vacía"}, status=status.HTTP_400_BAD_REQUEST)

            # Nombre personalizado opcional
            name = (request.data.get('name') or 'Test Personalizado').strip() or 'Test Personalizado'
            purpose = "Evaluación conversacional con preguntas definidas por el administrador"
            # Instrucciones para que la IA pregunte exactamente estas preguntas en orden
            ai_prompt = (
                "Actúa como entrevistador. Debes realizar las siguientes preguntas en orden, "
                "siempre una a la vez. No avances a la siguiente hasta que el usuario responda. "
                "Si la respuesta es breve o ambigua, pide una aclaración breve. Preguntas: "
                + " " + "; ".join(cleaned)
            )
            criteria = {
                "comprension": "Comprende y responde de forma adecuada a cada pregunta.",
                "profundidad": "Aporta detalles y ejemplos cuando corresponde.",
                "comunicacion": "Claridad y estructura en las respuestas."
            }

        test = Test.objects.create(
            name=name,
            purpose=purpose,
            ai_prompt_instructions=ai_prompt,
            evaluation_criteria=criteria,
            creator=request.user,
        )

        return Response({
            "message": "Test personalizado creado",
            "test_id": test.id,
            "name": test.name,
        }, status=status.HTTP_201_CREATED)


class ExportTestsByUserView(APIView):
    # Exporta todas las ejecuciones de un usuario a JSON (solo admin)
    def get(self, request):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        username = request.query_params.get('username')
        if not username:
            return Response({"error": "Parámetro 'username' requerido"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(username=username).first()
        if not user:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        executions = TestExecution.objects.filter(user=user).order_by('-start_time')
        data = []
        for ex in executions:
            data.append({
                "execution_id": ex.id,
                "user": ex.user.username,
                "test": ex.test.name,
                "start_time": ex.start_time,
                "finish_time": ex.finish_time,
                "chat_log": ex.chat_log,
                "evaluation_result": ex.evaluation_result,
            })

        return Response({
            "username": username,
            "count": executions.count(),
            "executions": data,
        }, status=status.HTTP_200_OK)


class ListUsersWithExecutionsView(APIView):
    # Lista usuarios que tienen ejecuciones, con conteo (solo admin)
    def get(self, request):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        users = User.objects.filter(testexecution__isnull=False).annotate(exec_count=Count('testexecution')).order_by('-exec_count', 'username')
        data = [{
            "id": u.id,
            "username": u.username,
            "full_name": (f"{u.first_name} {u.last_name}".strip() or u.username),
            "exec_count": u.exec_count,
        } for u in users]

        return Response({
            "count": len(data),
            "users": data,
        }, status=status.HTTP_200_OK)


class ListTestsView(APIView):
    # Lista todos los tests disponibles (solo admin)
    def get(self, request):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        tests = Test.objects.all().order_by('id')
        data = [{
            "id": t.id,
            "name": t.name,
            "purpose": t.purpose,
        } for t in tests]

        return Response({
            "count": len(data),
            "tests": data,
        }, status=status.HTTP_200_OK)


class DeleteTestView(APIView):
    # Elimina un test por ID (solo admin)
    def delete(self, request, test_id):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return Response({"error": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        test = Test.objects.filter(id=test_id).first()
        if not test:
            return Response({"error": "Test no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        # Al eliminar el Test, las ejecuciones asociadas se borran por cascade
        test.delete()
        return Response({"message": "Test eliminado", "test_id": test_id}, status=status.HTTP_200_OK)