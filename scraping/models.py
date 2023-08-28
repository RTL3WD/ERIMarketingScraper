from django.db import models

# Create your models here.
class Lead(models.Model):
    first_name = models.CharField(max_length=200,default='', blank=True)
    last_name = models.CharField(max_length=200,default='', blank=True)
    email = models.EmailField(default='', blank=True)
    phone = models.CharField(max_length=200,default='', blank=True)
    creditor_name = models.CharField(max_length=200,default='', blank=True)
    company_suied = models.CharField(max_length=200,default='', blank=True)
    folder_id = models.CharField(max_length=200,default='', blank=True)
    airtable_id = models.CharField(max_length=200,default='', blank=True)
    price = models.CharField(max_length=200,default='', blank=True)
    county = models.CharField(max_length=200,default='', blank=True)
    status = models.CharField(max_length=200,default='', blank=True)
    business_address = models.CharField(max_length=200,default='', blank=True)
    date = models.CharField(max_length=200,default='', blank=True)

    def __str__(self):
        if self.first_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return "No Title"
    
    
class CronJobs(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=200)
    log = models.CharField(max_length=200)