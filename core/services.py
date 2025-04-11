import cv2
import pytesseract
import numpy as np
from PIL import Image
import google.generativeai as genai
import os
from django.conf import settings
from io import BytesIO

# Configure PyTesseract
pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

# Configure Google Gemini API
try:
    if settings.GOOGLE_API_KEY:
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-2.0-flash') # Use appropriate model
    else:
        gemini_model = None
        print("Warning: GOOGLE_API_KEY not found in environment variables. Gemini enhancement disabled.")
except Exception as e:
    gemini_model = None
    print(f"Warning: Failed to configure Google Gemini API: {e}. Enhancement disabled.")


def preprocess_image(image_path):
    """Applies standard preprocessing: grayscale, thresholding."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image file: {image_path}")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Apply adaptive thresholding for potentially better results on varied lighting
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, 11, 2)

        # Optional: Denoising (can sometimes hurt OCR if too aggressive)
        # denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        # return denoised
        return thresh # Return the thresholded image (NumPy array)
    except Exception as e:
        print(f"Error during preprocessing image {image_path}: {e}")
        raise


def perform_ocr(image_data):
    """Performs OCR using PyTesseract on a preprocessed image (NumPy array or PIL Image)."""
    try:
        # Convert NumPy array from OpenCV to PIL Image if necessary
        if isinstance(image_data, np.ndarray):
            pil_image = Image.fromarray(cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB))
        elif isinstance(image_data, Image.Image):
             pil_image = image_data
        else:
             # Assume it's already a PIL image or compatible format if not ndarray
             pil_image = image_data # Or handle error

        # Perform OCR
        custom_config = r'--oem 3 --psm 6' # Example config, adjust as needed
        text = pytesseract.image_to_string(pil_image, config=custom_config)
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        print(f"Error: Tesseract executable not found at '{settings.TESSERACT_CMD}'. Please check configuration.")
        raise
    except Exception as e:
        print(f"Error during OCR: {e}")
        raise


def enhance_with_gemini(image_path, ocr_text):
    """Uses Gemini to analyze the image and OCR text for corrections and structure."""
    if not gemini_model:
        print("Gemini enhancement skipped: Model not configured.")
        return "Gemini enhancement disabled." # Return placeholder or ocr_text

    try:
        print(f"Starting Gemini enhancement for {image_path}")
        img = Image.open(image_path)

        # Ensure image is in a format Gemini supports (e.g., RGB)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Prepare prompt for Gemini
        prompt = f"""
Analyze the provided image and the following OCR text extracted from it.
Your goal is to improve the accuracy and structure of the text based on the visual layout in the image.

**Instructions:**
1.  **Identify and Correct Errors:** Correct any misrecognized characters, words, or formatting issues in the OCR text by comparing it with the image content.
2.  **Preserve Layout:** Maintain the original structure (paragraphs, lists, tables if any) as seen in the image. Use Markdown for formatting lists and simple tables if appropriate.
3.  **Contextual Understanding:** Use the visual context to resolve ambiguities in the text.
4.  **Output ONLY the corrected and formatted text.** Do not include any explanations, apologies, or introductory phrases like "Here is the corrected text:".

**OCR Text:**
{ocr_text}

**Corrected and Formatted Text:**
"""
        # Use the multimodal capabilities
        response = gemini_model.generate_content([prompt, img], stream=False) # Use stream=False for simpler handling here
        response.resolve() # Ensure the response is fully generated

        print(f"Gemini response received for {image_path}")
        # Basic check if response contains text
        if response.parts:
             # Assuming the text part is the primary content
             enhanced_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))
             return enhanced_text.strip()
        elif hasattr(response, 'text'):
             return response.text.strip()
        else:
             print(f"Warning: Gemini response for {image_path} did not contain expected text format.")
             # Fallback or specific error handling
             # Check response.prompt_feedback for safety ratings etc.
             if response.prompt_feedback.block_reason:
                 print(f"Gemini request blocked: {response.prompt_feedback.block_reason}")
                 return f"Gemini processing failed: Blocked ({response.prompt_feedback.block_reason})"
             return "Gemini enhancement failed: No text found in response."


    except Exception as e:
        print(f"Error during Gemini enhancement for {image_path}: {e}")
        # Consider more specific error handling based on google.api_core.exceptions
        return f"Gemini enhancement failed: {str(e)}"

def merge_results(tesseract_text, gemini_text):
    """Basic strategy to merge results. Prefers Gemini if available and seems valid."""
    if gemini_text and not gemini_text.startswith("Gemini enhancement failed") and not gemini_text.startswith("Gemini enhancement disabled"):
        # Add more sophisticated checks if needed (e.g., length comparison, keyword checks)
        return gemini_text
    return tesseract_text # Fallback to tesseract