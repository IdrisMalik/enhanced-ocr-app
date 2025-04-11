from celery import shared_task
from django.utils import timezone
from django.core.files.base import ContentFile
import os
import time
import pytesseract

from .models import ProcessedImage
from .services import preprocess_image, perform_ocr, enhance_with_gemini, merge_results

@shared_task(bind=True)
def process_image_task(self, image_id):
    """Celery task to process a single uploaded image."""
    try:
        image_instance = ProcessedImage.objects.get(id=image_id)
        image_instance.task_id = self.request.id
        image_instance.status = ProcessedImage.StatusChoices.PROCESSING
        image_instance.save(update_fields=['status', 'task_id'])

        image_path = image_instance.image.path
        print(f"Task {self.request.id}: Processing image ID {image_id} at path {image_path}")

        if not os.path.exists(image_path):
             raise FileNotFoundError(f"Image file not found at {image_path}")

        # 1. Preprocess Image
        print(f"Task {self.request.id}: Preprocessing...")
        preprocessed_image_data = preprocess_image(image_path)

        # 2. Perform OCR (PyTesseract)
        print(f"Task {self.request.id}: Performing OCR...")
        tesseract_text = perform_ocr(preprocessed_image_data)
        image_instance.tesseract_text = tesseract_text
        image_instance.save(update_fields=['tesseract_text'])
        print(f"Task {self.request.id}: OCR Complete.")

        # 3. Enhance with AI (Gemini)
        print(f"Task {self.request.id}: Enhancing with Gemini...")
        gemini_text = enhance_with_gemini(image_path, tesseract_text)
        image_instance.gemini_text = gemini_text
        image_instance.save(update_fields=['gemini_text'])
        print(f"Task {self.request.id}: Gemini Enhancement Complete.")

        # 4. Merge Results (Simple strategy for now)
        final_text = merge_results(tesseract_text, gemini_text)
        image_instance.final_text = final_text

        # 5. Finalize
        image_instance.status = ProcessedImage.StatusChoices.COMPLETED
        image_instance.processed_at = timezone.now()
        image_instance.save(update_fields=['final_text', 'status', 'processed_at'])
        print(f"Task {self.request.id}: Processing successful for image ID {image_id}")
        return {'status': 'COMPLETED', 'image_id': image_id}

    except FileNotFoundError as e:
         print(f"Task {self.request.id}: FAILED for image ID {image_id}. Error: {e}")
         try:
             image_instance = ProcessedImage.objects.get(id=image_id)
             image_instance.status = ProcessedImage.StatusChoices.FAILED
             image_instance.final_text = f"Processing failed: {e}"
             image_instance.processed_at = timezone.now()
             image_instance.save(update_fields=['status', 'final_text', 'processed_at'])
         except ProcessedImage.DoesNotExist:
             print(f"Task {self.request.id}: FAILED. Could not find ProcessedImage with ID {image_id} to update status.")
         # No need to retry if file is missing
         return {'status': 'FAILED', 'image_id': image_id, 'error': str(e)}

    except pytesseract.TesseractNotFoundError as e:
         print(f"Task {self.request.id}: FAILED for image ID {image_id}. Tesseract Error: {e}")
         # Handle Tesseract not found specifically
         try:
             image_instance = ProcessedImage.objects.get(id=image_id)
             image_instance.status = ProcessedImage.StatusChoices.FAILED
             image_instance.final_text = f"Processing failed: Tesseract not found or configured correctly. Check TESSERACT_CMD in .env and ensure Tesseract is installed."
             image_instance.processed_at = timezone.now()
             image_instance.save(update_fields=['status', 'final_text', 'processed_at'])
         except ProcessedImage.DoesNotExist:
             pass # Already logged above
         return {'status': 'FAILED', 'image_id': image_id, 'error': str(e)}

    except Exception as e:
        print(f"Task {self.request.id}: FAILED for image ID {image_id}. Error: {e}")
        # Generic error handling
        try:
            image_instance = ProcessedImage.objects.get(id=image_id)
            image_instance.status = ProcessedImage.StatusChoices.FAILED
            image_instance.final_text = f"Processing failed: {e}"
            image_instance.processed_at = timezone.now()
            image_instance.save(update_fields=['status', 'final_text', 'processed_at'])
        except ProcessedImage.DoesNotExist:
             print(f"Task {self.request.id}: FAILED. Could not find ProcessedImage with ID {image_id} to update status.")
        # Optional: Retry logic for transient errors (e.g., network issues with Gemini)
        # raise self.retry(exc=e, countdown=60, max_retries=3)
        return {'status': 'FAILED', 'image_id': image_id, 'error': str(e)}