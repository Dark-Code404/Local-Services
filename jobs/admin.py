from django.contrib import admin

from jobs.models import *

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Job)
admin.site.register(JobApplication)