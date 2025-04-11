# Django Enhanced OCR with Gemini AI

## Overview

This project is a Django web application designed for Optical Character Recognition (OCR) on uploaded images. It utilizes PyTesseract for initial text extraction and enhances the accuracy and structural understanding using Google's Gemini Pro Vision multimodal AI model. The application supports batch image uploads, processes them asynchronously using Celery and Redis, and provides a user-friendly interface to view the original image alongside the final extracted text.

## Key Features

*   **Batch Image Upload:** Upload multiple images simultaneously via a drag-and-drop interface or file selector.
*   **Standardized Preprocessing:** Images are preprocessed using OpenCV (grayscale, adaptive thresholding) for optimized OCR performance.
*   **Dual-Engine OCR:**
    *   Initial fast OCR using PyTesseract.
    *   AI-powered enhancement using Google Gemini API to analyze image layout, correct errors, and improve text structure.
*   **Asynchronous Processing:** Long-running OCR and AI tasks are handled in the background using Celery workers, preventing UI blocking. Redis is used as the message broker and result backend.
*   **Side-by-Side Preview:** View the original uploaded image next to the final, enhanced text output.
*   **Result Actions:** Easily copy the extracted text to the clipboard or download it as a `.txt` file.
*   **Status Tracking:** Real-time feedback on the processing status of each image (Pending, Processing, Completed, Failed).
*   **Modular Django Structure:** Organized codebase following Django best practices (`core` app, `services.py`, Celery tasks).
*   **Environment Configuration:** Securely manage settings and API keys using a `.env` file.

## Technology Stack

*   **Backend:** Python 3.10+, Django 4.x
*   **OCR:** Tesseract-OCR, PyTesseract
*   **Image Processing:** OpenCV (opencv-python-headless), Pillow
*   **AI Enhancement:** Google Generative AI SDK (`google-generativeai`), Gemini Pro Vision API
*   **Asynchronous Tasks:** Celery, Redis (as Broker & Result Backend)
*   **Task Execution (Windows):** Eventlet
*   **Environment Variables:** python-dotenv
*   **Frontend:** HTML, CSS (Bootstrap 5), JavaScript (Vanilla JS for uploads & polling)
*   **Database:** SQLite (default, configurable in Django settings)
*   **WSGI Server (Development):** Django Development Server

## Prerequisites

Before setting up the project, ensure you have the following installed on your Windows 11 system:

1.  **Python:** Version 3.10 or newer. Download from [python.org](https://www.python.org/) and ensure it's added to your system PATH during installation.
2.  **Tesseract-OCR:**
    *   Download the installer from the [Tesseract GitHub Wiki](https://github.com/UB-Mannheim/tesseract/wiki) (e.g., `tesseract-ocr-w64-setup-*.exe`).
    *   **Important:** During installation, ensure you select the option to **add Tesseract to the system PATH**.
    *   Verify the installation path (e.g., `C:\Program Files\Tesseract-OCR`).
    *   Verify installation by opening PowerShell and running `tesseract --version`.
3.  **Docker Desktop:** Required for running the Redis container easily. Download from [Docker Hub](https://www.docker.com/products/docker-desktop/).
4.  **Git (Optional):** For cloning the repository.

## Setup Instructions (Windows 11 / PowerShell)

1.  **Clone or Download:** Get the project code:
    ```powershell
    # If using Git
    git clone <repository_url> django_ocr_project
    cd django_ocr_project

    # Or download and extract the ZIP file, then navigate into the directory
    cd path\to\django_ocr_project
    ```

2.  **Start Redis Container:** Open Docker Desktop (ensure it's running) and start a Redis container in PowerShell:
    ```powershell
    docker run -d -p 6379:6379 --name my-redis redis:latest
    ```
    *   Verify it's running: `docker ps` (you should see `my-redis`).

3.  **Create Virtual Environment:**
    ```powershell
    python -m venv venv
    ```

4.  **Activate Virtual Environment:**
    ```powershell
    .\venv\Scripts\Activate.ps1
    ```
    *(Your prompt should now start with `(venv)`)*

5.  **Install Dependencies:**
    ```powershell
    pip install -r requirements.txt
    ```
    *(This includes Django, Celery, Redis client, OpenCV, PyTesseract, Google AI SDK, python-dotenv, and eventlet)*

6.  **Configure Environment Variables:**
    *   Rename the `.env.template` file to `.env`.
    *   Open `.env` in a text editor and fill in the values:
        *   `SECRET_KEY`: Generate a strong, unique secret key (e.g., using Python's `secrets` module or an online generator).
        *   `DEBUG`: Set to `True` for development, `False` for production.
        *   `ALLOWED_HOSTS`: Keep `127.0.0.1,localhost` for local development.
        *   `GOOGLE_API_KEY`: Your API key obtained from [Google AI Studio](https://aistudio.google.com/app/apikey) or Google Cloud Console. Ensure the Gemini API is enabled.
        *   `CELERY_BROKER_URL`: Should be `redis://127.0.0.1:6379/0` (using the IP address is recommended on Windows).
        *   `CELERY_RESULT_BACKEND`: Should be `redis://127.0.0.1:6379/0`.
        *   `TESSERACT_CMD`: The **full path** to your `tesseract.exe`. Use double backslashes (`\\`). Example: `C:\\Program Files\\Tesseract-OCR\\tesseract.exe`. Verify this path matches your installation.

7.  **Database Migrations:** Apply the database schema:
    ```powershell
    python manage.py makemigrations core
    python manage.py migrate
    ```

8.  **Create Superuser (Optional):** To access the Django admin interface (`/admin/`):
    ```powershell
    python manage.py createsuperuser
    ```
    *(Follow the prompts)*

## Running the Application

You need to run two processes simultaneously in separate PowerShell terminals (ensure the virtual environment is activated in both).

1.  **Terminal 1: Start the Celery Worker:**
    ```powershell
    # Navigate to the project directory if needed
    # Activate venv: .\venv\Scripts\Activate.ps1
    celery -A config worker --loglevel=info -P eventlet
    ```
    *   The `-P eventlet` flag is crucial for running Celery smoothly on Windows.

2.  **Terminal 2: Start the Django Development Server:**
    ```powershell
    # Navigate to the project directory if needed
    # Activate venv: .\venv\Scripts\Activate.ps1
    python manage.py runserver
    ```

## Usage

1.  Ensure the Redis container, Celery worker, and Django server are all running.
2.  Open your web browser and go to `http://127.0.0.1:8000/`.
3.  Drag and drop image files onto the drop zone or click it to select files using the file browser.
4.  Placeholders for each image will appear, showing the processing status.
5.  Once an image is processed (`COMPLETED`), the extracted text will be displayed next to the image preview.
6.  Use the "Copy Text" or "Download Text" buttons below the extracted text.
7.  If processing fails (`FAILED`), an error message will be displayed. Check the Celery worker logs for more details.

## Project Structure

```
django_ocr_project/
├── config/             # Django project configuration
│   ├── __init__.py
│   ├── settings.py     # Main settings
│   ├── urls.py         # Root URL patterns
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py       # Celery app configuration
├── core/               # Main application logic
│   ├── __init__.py
│   ├── admin.py        # Admin site configuration
│   ├── apps.py
│   ├── models.py       # Database models (ProcessedImage)
│   ├── views.py        # View functions/classes
│   ├── urls.py         # App-specific URL patterns
│   ├── tasks.py        # Celery task definitions
│   ├── services.py     # Business logic (preprocessing, OCR, Gemini)
│   └── migrations/
├── static/             # Static files (CSS, JS)
│   └── js/
│       └── upload.js   # Frontend logic
│   └── css/
│       └── style.css
├── templates/          # HTML templates
│   └── core/
│       └── upload.html # Main upload page template
├── media/              # User uploaded files (created automatically)
│   └── uploads/
├── manage.py           # Django management script
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (GITIGNORE this!)
└── .env.template       # Template for .env file
```