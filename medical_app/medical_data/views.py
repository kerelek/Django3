import os
import json
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from django.db import IntegrityError
from django.db.models import Q
from .forms import MedicalRecordForm, JSONUploadForm, MedicalRecordEditForm
from .models import MedicalRecord, JSONFile

def home(request):
    return render(request, 'medical_data/home.html')

def create_medical_record(request):
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            save_location = form.cleaned_data['save_location']
            record_data = {
                'patient_name': form.cleaned_data['patient_name'],
                'age': form.cleaned_data['age'],
                'gender': form.cleaned_data['gender'],
                'height': form.cleaned_data['height'],
                'weight': form.cleaned_data['weight'],
                'blood_pressure': form.cleaned_data['blood_pressure'],
                'heart_rate': form.cleaned_data['heart_rate'],
                'temperature': form.cleaned_data['temperature'],
                'symptoms': form.cleaned_data['symptoms'],
                'diagnosis': form.cleaned_data['diagnosis'],
            }
            
            record_id = uuid.uuid4()
            json_data = {
                'id': str(record_id),
                **record_data,
                'created_at': timezone.now().isoformat()
            }
            
            duplicate = None
            if save_location in ['db', 'both']:
                duplicate = MedicalRecord.objects.filter(
                    patient_name=record_data['patient_name'],
                    age=record_data['age'],
                    gender=record_data['gender'],
                    height=record_data['height'],
                    weight=record_data['weight'],
                    diagnosis=record_data['diagnosis']
                ).first()
            
            if duplicate and save_location in ['db', 'both']:
                messages.warning(request, 'Такая запись уже существует в базе данных!')
                return render(request, 'medical_data/create_record.html', {'form': form})
            
            db_saved = False
            if save_location in ['db', 'both'] and not duplicate:
                try:
                    MedicalRecord.objects.create(
                        id=record_id,
                        **record_data,
                        data_source='db' if save_location == 'db' else 'both'
                    )
                    db_saved = True
                    messages.success(request, 'Запись сохранена в базу данных!')
                except IntegrityError:
                    messages.error(request, 'Ошибка при сохранении в базу данных!')
            
            file_saved = False
            if save_location in ['file', 'both']:
                json_dir = os.path.join(settings.MEDIA_ROOT, 'medical_json')
                os.makedirs(json_dir, exist_ok=True)
                
                filename = f"medical_record_{record_id}.json"
                filepath = os.path.join(json_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                
                file_saved = True
                messages.success(request, f'Запись сохранена в файл: {filename}')
            
            if db_saved or file_saved:
                return redirect('view_records')
            else:
                messages.error(request, 'Не удалось сохранить запись!')
    
    else:
        form = MedicalRecordForm()
    
    return render(request, 'medical_data/create_record.html', {'form': form})

def upload_json_file(request):
    if request.method == 'POST':
        form = JSONUploadForm(request.POST, request.FILES)
        if form.is_valid():
            json_file = form.save(commit=False)
            
            try:
                file_content = json_file.file.read().decode('utf-8')
                data = json.loads(file_content)
                
                required_fields = ['patient_name', 'age', 'gender', 'height', 'weight']
                for field in required_fields:
                    if field not in data:
                        raise ValueError(f"Отсутствует обязательное поле: {field}")
                
                duplicate = MedicalRecord.objects.filter(
                    patient_name=data['patient_name'],
                    age=data['age'],
                    gender=data['gender'],
                    height=data['height'],
                    weight=data['weight'],
                    diagnosis=data.get('diagnosis', '')
                ).first()
                
                if duplicate:
                    messages.warning(request, 'Такая запись уже существует в базе данных!')
                    return redirect('upload_json')
                
                json_file.is_valid = True
                json_file.save()
                
                MedicalRecord.objects.create(
                    id=uuid.uuid4(),
                    patient_name=data['patient_name'],
                    age=data['age'],
                    gender=data['gender'],
                    height=data['height'],
                    weight=data['weight'],
                    blood_pressure=data.get('blood_pressure', ''),
                    heart_rate=data.get('heart_rate', 0),
                    temperature=data.get('temperature', 36.6),
                    symptoms=data.get('symptoms', ''),
                    diagnosis=data.get('diagnosis', ''),
                    data_source='file',
                    created_at=timezone.now()
                )
                
                messages.success(request, 'Файл успешно загружен и проверен!')
                
            except (json.JSONDecodeError, ValueError, UnicodeDecodeError) as e:
                if json_file.file and os.path.isfile(json_file.file.path):
                    os.remove(json_file.file.path)
                messages.error(request, f'Ошибка в файле: {str(e)}')
                return redirect('upload_json')
            
            return redirect('view_records')
    else:
        form = JSONUploadForm()
    
    return render(request, 'medical_data/upload_json.html', {'form': form})

def view_json_files(request):
    json_dir = os.path.join(settings.MEDIA_ROOT, 'medical_json')
    
    if not os.path.exists(json_dir):
        messages.info(request, 'Папка с JSON файлами не существует.')
        return render(request, 'medical_data/view_files.html', {'files': []})
    
    json_files = []
    try:
        for filename in os.listdir(json_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(json_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        json_files.append({
                            'filename': filename,
                            'data': data,
                            'filepath': filepath,
                            'size': os.path.getsize(filepath)
                        })
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
    except FileNotFoundError:
        messages.info(request, 'Папка с JSON файлами не найдена.')
    
    if not json_files:
        messages.info(request, 'Нет доступных JSON файлов.')
    
    return render(request, 'medical_data/view_files.html', {'files': json_files})

def view_medical_records(request):
    data_source = request.GET.get('source', 'db')
    
    if data_source == 'file':
        return view_json_files(request)
    else:
        records = MedicalRecord.objects.all().order_by('-created_at')
        return render(request, 'medical_data/view_records.html', {
            'records': records,
            'data_source': data_source
        })

def search_records(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        query = request.GET.get('q', '')
        if query:
            records = MedicalRecord.objects.filter(
                Q(patient_name__icontains=query) |
                Q(symptoms__icontains=query) |
                Q(diagnosis__icontains=query) |
                Q(blood_pressure__icontains=query)
            ).order_by('-created_at')
            
            results = []
            for record in records:
                results.append({
                    'id': str(record.id),
                    'patient_name': record.patient_name,
                    'age': record.age,
                    'gender': record.get_gender_display(),
                    'height': record.height,
                    'weight': record.weight,
                    'blood_pressure': record.blood_pressure,
                    'heart_rate': record.heart_rate,
                    'temperature': record.temperature,
                    'symptoms': record.symptoms,
                    'diagnosis': record.diagnosis,
                    'bmi': record.bmi,
                    'created_at': record.created_at.strftime('%d.%m.%Y %H:%M')
                })
            
            return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})

def edit_record(request, record_id):
    record = get_object_or_404(MedicalRecord, id=record_id)
    
    if request.method == 'POST':
        form = MedicalRecordEditForm(request.POST, instance=record)
        if form.is_valid():
            duplicate = MedicalRecord.objects.filter(
                patient_name=form.cleaned_data['patient_name'],
                age=form.cleaned_data['age'],
                gender=form.cleaned_data['gender'],
                height=form.cleaned_data['height'],
                weight=form.cleaned_data['weight'],
                diagnosis=form.cleaned_data['diagnosis']
            ).exclude(id=record.id).first()
            
            if duplicate:
                messages.error(request, 'Такая запись уже существует!')
            else:
                form.save()
                messages.success(request, 'Запись успешно обновлена!')
                return redirect('view_records')
    else:
        form = MedicalRecordEditForm(instance=record)
    
    return render(request, 'medical_data/edit_record.html', {
        'form': form,
        'record': record
    })

def delete_record(request, record_id):
    record = get_object_or_404(MedicalRecord, id=record_id)
    
    if request.method == 'POST':
        record.delete()
        messages.success(request, 'Запись успешно удалена!')
        return redirect('view_records')
    
    return render(request, 'medical_data/delete_record.html', {'record': record})
