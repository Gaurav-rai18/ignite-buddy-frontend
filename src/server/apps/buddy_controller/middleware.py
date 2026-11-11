from django.http import JsonResponse

from .models import ExamControl


class ExamModeMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        try:
            exam_control = ExamControl.objects.first()

            if (
                exam_control
                and exam_control.is_exam_active
            ):

                blocked_prefixes = [
                    "/api/chat/",
                    "/api/assignments/",
                ]

                if any(
                    request.path.startswith(path)
                    for path in blocked_prefixes
                ):
                    return JsonResponse(
                        {
                            "success": False,
                            "message": (
                                "Ignite Buddy is disabled "
                                "during assessment."
                            )
                        },
                        status=403
                    )

        except Exception:
            pass

        return self.get_response(request)
