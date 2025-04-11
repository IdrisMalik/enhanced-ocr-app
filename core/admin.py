from django.contrib import admin
from .models import ProcessedImage

@admin.register(ProcessedImage)
class ProcessedImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'original_filename', 'status', 'uploaded_at', 'processed_at', 'task_id')
    list_filter = ('status', 'uploaded_at')
    search_fields = ('original_filename', 'task_id')
    readonly_fields = ('uploaded_at', 'processed_at', 'tesseract_text', 'gemini_text', 'final_text', 'image_preview')
    fieldsets = (
        (None, {'fields': ('original_filename', 'status', 'task_id')}),
        ('Files', {'fields': ('image', 'image_preview')}),
        ('Timestamps', {'fields': ('uploaded_at', 'processed_at')}),
        ('Results', {'fields': ('tesseract_text', 'gemini_text', 'final_text')}),
    )

    def image_preview(self, obj):
        from django.utils.html import format_html
        if obj.image:
            return format_html('<img src="{}" width="150" height="auto" />', obj.image.url)
        return "(No image)"
    image_preview.short_description = 'Preview'