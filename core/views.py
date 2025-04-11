from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, View
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

from .models import ProcessedImage
from .tasks import process_image_task

class UploadView(TemplateView):
    template_name = 'core/upload.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Enhanced OCR Upload'
        return context

# Use csrf_exempt only if you understand the implications or handle CSRF via JS headers
# For simplicity in this example, we exempt it, but in production, configure CSRF properly.
@method_decorator(csrf_exempt, name='dispatch')
class ProcessImagesView(View):
    def post(self, request, *args, **kwargs):
        if not request.FILES:
            return HttpResponseBadRequest("No files were uploaded.")

        uploaded_files = request.FILES.getlist('images') # Match the name in FormData
        image_ids = []
        task_ids = []

        for uploaded_file in uploaded_files:
            # Create a ProcessedImage instance
            image_instance = ProcessedImage.objects.create(
                image=uploaded_file,
                original_filename=uploaded_file.name # Store original name here
            )
            image_ids.append(image_instance.id)

            # Trigger the Celery task
            task = process_image_task.delay(image_instance.id)
            task_ids.append(task.id)

            # Optionally link task_id back immediately if needed,
            # but the task itself also updates it.
            # image_instance.task_id = task.id
            # image_instance.save(update_fields=['task_id'])


        return JsonResponse({'status': 'success', 'image_ids': image_ids, 'task_ids': task_ids})

class GetResultView(View):
     def get(self, request, pk, *args, **kwargs):
        try:
            image_instance = get_object_or_404(ProcessedImage, pk=pk)
            response_data = {
                'id': image_instance.id,
                'status': image_instance.status,
                'imageUrl': image_instance.image.url if image_instance.image else None,
                'filename': image_instance.original_filename,
            }
            if image_instance.status == ProcessedImage.StatusChoices.COMPLETED:
                response_data['finalText'] = image_instance.final_text
            elif image_instance.status == ProcessedImage.StatusChoices.FAILED:
                 response_data['error'] = image_instance.final_text # Store error message here

            return JsonResponse(response_data)
        except ProcessedImage.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Image not found'}, status=404)
        except Exception as e:
             return JsonResponse({'status': 'error', 'message': str(e)}, status=500)