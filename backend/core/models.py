from django.db import models

class Broadcast(models.Model):
    title = models.CharField(max_length=160)
    message = models.TextField()
    audience = models.CharField(max_length=40, default='All students')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return self.title

class ScheduledLink(models.Model):
    title = models.CharField(max_length=160)
    onedrive_url = models.URLField(max_length=1000)
    publish_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['publish_at']
    def __str__(self):
        return self.title

class SiteSetting(models.Model):
    key = models.CharField(max_length=80, unique=True)
    value = models.CharField(max_length=200, default='false')
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f'{self.key}: {self.value}'
