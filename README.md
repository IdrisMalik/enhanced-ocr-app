# Django Enhanced OCR Application

## Overview

This project is a web application built with Django that performs Optical Character Recognition (OCR) on uploaded images. It utilizes PyTesseract for initial text extraction and integrates with the Google Gemini API for multimodal analysis to enhance the accuracy and structural understanding of the extracted text. The application processes uploads asynchronously using Celery and provides a user interface for batch image uploads and viewing results.

## Features

*   **Image Upload**: Supports single or multiple image file uploads via a drag-and-drop interface or file selection.
*   **Image Preprocessing**: Applies standard image preprocessing techniques (grayscale conversion, thresholding) using OpenCV and Pillow to optimize images for OCR.
*   **OCR Engine**: Uses PyTesseract to extract text content from the preprocessed images.
*   **AI Enhancement**: Leverages the Google Gemini multimodal model to analyze the original image alongside the initial OCR output, correcting errors and improving layout/structure recognition.
*   **Asynchronous Processing**: Offloads OCR and AI analysis tasks to a Celery queue (with Redis as a broker/backend) for non-blocking background processing.
*   **Result Display**: Presents the final, enhanced text output side-by-side with the original uploaded image.
*   **User Interface**: Provides a clean web interface built with Django templates and JavaScript for interaction, including status updates via polling and options to copy or download the extracted text.

## Technology Stack

*   **Backend**: Python, Django
*   **Asynchronous Tasks**: Celery, Redis
*   **OCR**: PyTesseract, Tesseract-OCR Engine
*   **Image Processing**: OpenCV-Python, Pillow
*   **AI Model**: Google Gemini API (`google-generativeai`)
*   **Frontend**: HTML, CSS (Bootstrap), JavaScript
*   **Database**: SQLite (default, configurable in Django settings)
*   **Environment Management**: `python-dotenv`

## Project Structure

```
django_ocr_project/
├── config/             # Django project settings, URLs, Celery config
├── core/               # Main application logic (models, views, tasks, services)
├── static/             # Static assets (CSS, JavaScript)
├── templates/          # HTML templates
├── media/              # User uploaded files (created automatically)
├── manage.py           # Django management script
├── requirements.txt    # Python dependencies
└── .env                # Environment variables (create from .env.template)
```

## Setup and Installation

1.  **Prerequisites**:
    *   Python 3.10+
    *   Tesseract-OCR Engine (installed and added to system PATH)
    *   Redis Server (running, e.g., via Docker: `docker run -d -p 6379:6379 redis:latest`)
    *   Google API Key with Gemini API enabled.

2.  **Clone the Repository**:
    ```bash
    git clone <repository-url> django_ocr_project
    cd django_ocr_project
    ```

3.  **Create and Activate Virtual Environment**:
    ```bash
    # Windows (PowerShell)
    python -m venv venv
    .\venv\Scripts\Activate.ps1

    # macOS / Linux (Bash)
    python3 -m venv venv
    source venv/bin/activate
    ```

4.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: On Windows, `eventlet` is included in `requirements.txt` for Celery compatibility.)*

5.  **Configure Environment Variables**:
    *   Copy `.env.template` to `.env`.
    *   Edit the `.env` file and provide values for:
        *   `SECRET_KEY` (Generate a secure key)
        *   `GOOGLE_API_KEY`
        *   `TESSERACT_CMD` (If Tesseract is not in the default PATH or installed in a non-standard location. Use double backslashes `\\` on Windows).
        *   Verify `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` point to your running Redis instance (use `redis://127.0.0.1:6379/0` if running locally).

6.  **Database Migrations**:
    ```bash
    python manage.py makemigrations core
    python manage.py migrate
    ```

7.  **Run Celery Worker**:
    *   Open a new terminal, activate the virtual environment.
    ```bash
    # Windows (PowerShell)
    celery -A config worker --loglevel=info -P eventlet

    # macOS / Linux (Bash)
    celery -A config worker --loglevel=info
    ```

8.  **Run Django Development Server**:
    *   In the original terminal (virtual environment active).
    ```bash
    python manage.py runserver
    ```

## Usage

1.  Ensure the Redis server, Celery worker, and Django development server are running.
2.  Access the application in your web browser, typically at `http://127.0.0.1:8000/`.
3.  Drag and drop image files onto the upload area or click to select files.
4.  The application will upload the images and display processing status.
5.  Once processing is complete, the enhanced text output will be shown alongside the image preview.
6.  Use the "Copy Text" or "Download Text" buttons for the results.

## Configuration

Key configuration options are managed via environment variables in the `.env` file:

*   `SECRET_KEY`: Django secret key.
*   `DEBUG`: Django debug mode (True/False).
*   `ALLOWED_HOSTS`: Allowed hostnames for the server.
*   `GOOGLE_API_KEY`: API key for Google Gemini.
*   `CELERY_BROKER_URL`: Connection URL for the Celery message broker (Redis).
*   `CELERY_RESULT_BACKEND`: Connection URL for the Celery result backend (Redis).
*   `TESSERACT_CMD`: Full path to the Tesseract executable if not in PATH.
