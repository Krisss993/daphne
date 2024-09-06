from django.db import models
from django.contrib.auth.models import User

class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_conversations')
    title = models.CharField(max_length=255, default="New Conversation")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation with {self.user.username} - {self.title}"

class ChatMessage(models.Model):
    conversation = models.ForeignKey(Conversation, related_name="chat_messages", on_delete=models.CASCADE)
    sender = models.CharField(max_length=255)  # 'user' or 'assistant'
    message = models.TextField()
    is_user_message = models.BooleanField(default=False)  # New column to track user message
    is_ai_message = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.message[:50]}..."
