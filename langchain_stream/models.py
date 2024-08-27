from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"

class ChatMessage(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=255)  # 'user' or 'ai'
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.message[:50]}..."
    
class UploadedFile(models.Model):
    conversation = models.ForeignKey('Conversation', on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='uploaded/', validators=[FileExtensionValidator(allowed_extensions=['pdf', 'txt'])])
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

    def file_size(self):
        return self.file.size
