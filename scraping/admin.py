from django.contrib import admin
from .models import Lead, CronJobs

admin.site.register(Lead)
admin.site.register(CronJobs)

# Register your models here.
