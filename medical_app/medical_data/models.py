import os
import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

def validate_json_extension(value):
    ext = os.path.splitext(value.name)[1]
    if ext.lower() != '.json':
        raise ValidationError('Разрешены только файлы JSON.')

def medical_json_file_path(instance, filename):
    ext = '.json'
    filename = f"medical_data_{uuid.uuid4()}{ext}"
    return os.path.join('medical_json', filename)

class MedicalRecord(models.Model):
    GENDER_CHOICES = [
        ('M', 'Мужской'),
        ('F', 'Женский'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient_name = models.CharField(max_length=100, verbose_name="Имя пациента")
    age = models.PositiveIntegerField(verbose_name="Возраст")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name="Пол")
    height = models.FloatField(verbose_name="Рост (см)")
    weight = models.FloatField(verbose_name="Вес (кг)")
    blood_pressure = models.CharField(max_length=10, verbose_name="Артериальное давление")
    heart_rate = models.PositiveIntegerField(verbose_name="Частота сердечных сокращений")
    temperature = models.FloatField(verbose_name="Температура тела (°C)")
    symptoms = models.TextField(verbose_name="Симптомы")
    diagnosis = models.CharField(max_length=200, verbose_name="Диагноз")
    created_at = models.DateTimeField(default=timezone.now)
    data_source = models.CharField(
        max_length=10, 
        choices=[('db', 'База данных'), ('file', 'Файл')],
        default='db'
    )
    
    def __str__(self):
        return f"{self.patient_name} - {self.diagnosis}"
    
    @property
    def bmi(self):
        if self.height > 0:
            return round(self.weight / ((self.height / 100) ** 2), 2)
        return 0

class JSONFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(
        upload_to=medical_json_file_path,
        validators=[validate_json_extension],
        verbose_name="JSON файл"
    )
    uploaded_at = models.DateTimeField(default=timezone.now)
    is_valid = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{os.path.basename(self.file.name)}"
    
    def delete(self, *args, **kwargs):
        if self.file and os.path.isfile(self.file.path):
            os.remove(self.file.path)
        super().delete(*args, **kwargs)
