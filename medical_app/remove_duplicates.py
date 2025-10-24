# remove_duplicates.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_app.settings')
django.setup()

from medical_data.models import MedicalRecord
from django.db.models import Count

# Находим дубликаты
duplicates = MedicalRecord.objects.values(
    'patient_name', 'age', 'gender', 'height', 'weight', 'diagnosis'
).annotate(
    count=Count('id')
).filter(count__gt=1)

print(f"Найдено групп дубликатов: {len(duplicates)}")

for dup in duplicates:
    print(f"Дубликаты для: {dup}")
    
    # Находим все записи с этими данными
    records = MedicalRecord.objects.filter(
        patient_name=dup['patient_name'],
        age=dup['age'],
        gender=dup['gender'],
        height=dup['height'],
        weight=dup['weight'],
        diagnosis=dup['diagnosis']
    ).order_by('created_at')
    
    # Оставляем самую старую запись, удаляем остальные
    keep_record = records.first()
    delete_records = records.exclude(id=keep_record.id)
    
    print(f"  Оставляем: {keep_record.id} (создана: {keep_record.created_at})")
    print(f"  Удаляем: {delete_records.count()} записей")
    
    delete_records.delete()

print("Дубликаты удалены!")
