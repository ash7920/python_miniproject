# models.py

from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    connections = models.ManyToManyField('self', symmetrical=True, blank=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    year = models.CharField(max_length=10)
    department = models.CharField(max_length=100)
    division = models.CharField(max_length=10)
    subject = models.CharField(max_length=100)
    def __str__(self):
        return self.user.username

class Connection(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    is_accepted = models.BooleanField(default=False)
    meet_scheduled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({'Accepted' if self.is_accepted else 'Pending'})"

class Note(models.Model):
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='notes/')

    def __str__(self):
        return self.title

class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    is_done = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Meeting(models.Model):
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE)
    scheduled_time = models.DateTimeField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Meeting with {self.connection.from_user.username} on {self.scheduled_time}"

