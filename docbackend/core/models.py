from django.db import models
from django.utils import timezone
import os
from django.conf import settings

class Document(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    file_id = models.CharField(max_length=255, unique=True)  # Appwrite file ID
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    file = models.FileField(upload_to='documents/%Y/%m/%d/', null=True, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    processed = models.BooleanField(default=False)
    extracted_text = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Additional metadata fields
    uploader_first_name = models.CharField(max_length=100, blank=True)
    uploader_last_name = models.CharField(max_length=100, blank=True)
    uploader_email = models.EmailField(blank=True)
    purpose = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)

    @property 
    def file_path(self):
        return os.path.join(settings.MEDIA_ROOT, self.file.name)

    def __str__(self):
        return self.file_name

class Classification(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='classifications')
    category = models.CharField(max_length=100)
    confidence = models.FloatField()
    classified_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.document.file_name} - {self.category}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('upload', 'Document Upload'),
        ('status_change', 'Status Change'),
    ]

    document = models.ForeignKey('Document', on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type} - {self.message[:50]}..."