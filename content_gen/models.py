from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class UserRequestTrack(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    difficulty = models.CharField(choices=[("easy", "EASY"), ("medium", "MEDIUM"), ("hard", "HARD")], max_length=10, null=True, blank=True)
    question_type = models.CharField(max_length=100)
    topic = models.CharField(max_length=100, null=True, blank=True)
    subtopic = models.CharField(max_length=100, null=True, blank=True)
    question_count = models.PositiveIntegerField()
    input_token = models.PositiveIntegerField()
    output_token = models.PositiveIntegerField()

class PromptUpdateTrack(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    original_prompt = models.TextField()
    updated_prompt = models.TextField()
    content_type = models.CharField(max_length=100)
