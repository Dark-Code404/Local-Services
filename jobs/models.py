from datetime import timezone
from django.db import models
from django.contrib.gis.db.models import PointField
from django.contrib.gis.db import models

from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.gis.geos import Point


class CustomUser(AbstractUser):
    role = models.CharField(max_length=10, choices=(('hire', 'Hire'), ('worker', 'Worker')))
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    groups = models.ManyToManyField(
        Group,
        related_name="customuser_groups",  
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_permissions",  
        blank=True,
    )


from django.contrib.gis.db.models import PointField
from geopy.geocoders import Nominatim

class Job(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=255)  # Text location
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)  # Geographic coordinates
    posted_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='posted_jobs')
    date_posted = models.DateField(auto_now=True)
    expiry_date = models.DateField(default='2024-01-01')
    required_workers = models.PositiveIntegerField(default=1)
    fulfilled = models.BooleanField(default=False)
    

    

    def __str__(self):
        return self.title
 

class JobApplication(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    worker = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='applications')
    name = models.CharField(max_length=100, null=True)
    email = models.EmailField(null=True)
    phone_number = models.CharField(max_length=15, default='98xxxxxxxx')
    status = models.CharField(max_length=20, default='Pending')   
    is_paid = models.BooleanField(default=False)
    

    def __str__(self):
        return f"{self.name} - {self.job.title}"