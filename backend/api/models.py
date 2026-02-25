
import uuid
from django.db import models

class ChatMessage(models.Model):
    session_id = models.UUIDField(default=uuid.uuid4, editable=False)
    business_type = models.CharField(max_length=20)
    role = models.CharField(max_length=20)  # user / assistant
    content = models.TextField()
    locations = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.session_id} - {self.role}"
