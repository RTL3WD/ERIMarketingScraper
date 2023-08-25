from django.db import models

# Create your models here.
class Lead(models.Model):
    first_name = models.CharField(max_length=100,default='')
    last_name = models.CharField(max_length=100,default='')
    email = models.EmailField(default='')
    phone = models.CharField(max_length=100,default='')
    creditor_name = models.CharField(max_length=100,default='')
    company_suied = models.CharField(max_length=100,default='')
    folder_id = models.CharField(max_length=100,default='')
    airtable_id = models.CharField(max_length=100,default='')
    price = models.CharField(max_length=100,default='')
    county = models.CharField(max_length=100,default='')
    status = models.CharField(max_length=100,default='')
    business_address = models.CharField(max_length=100,default='')
    date = models.CharField(max_length=100,default='')

    # def __str__(self):
    #     return f"{self.first_name} {self.last_name}"