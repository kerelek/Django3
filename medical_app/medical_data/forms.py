from django import forms
from django.core.exceptions import ValidationError
from .models import JSONFile, MedicalRecord

class MedicalRecordForm(forms.Form):
    SAVE_CHOICES = [
        ('db', 'Сохранить в базу данных'),
        ('file', 'Сохранить в JSON файл'),
        ('both', 'Сохранить и в базу и в файл'),
    ]
    
    save_location = forms.ChoiceField(
        choices=SAVE_CHOICES,
        initial='both',
        label="Куда сохранить данные",
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    patient_name = forms.CharField(
        max_length=100,
        label="Имя пациента",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={'required': 'Введите имя пациента'}
    )
    
    age = forms.IntegerField(
        min_value=0,
        max_value=150,
        label="Возраст",
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Введите возраст',
            'min_value': 'Возраст не может быть отрицательным',
            'max_value': 'Возраст не может превышать 150 лет'
        }
    )
    
    gender = forms.ChoiceField(
        choices=[('M', 'Мужской'), ('F', 'Женский')],
        label="Пол",
        widget=forms.Select(attrs={'class': 'form-control'}),
        error_messages={'required': 'Выберите пол'}
    )
    
    height = forms.FloatField(
        min_value=50,
        max_value=300,
        label="Рост (см)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        error_messages={
            'required': 'Введите рост',
            'min_value': 'Рост должен быть не менее 50 см',
            'max_value': 'Рост не может превышать 300 см'
        }
    )
    
    weight = forms.FloatField(
        min_value=1,
        max_value=500,
        label="Вес (кг)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        error_messages={
            'required': 'Введите вес',
            'min_value': 'Вес должен быть не менее 1 кг',
            'max_value': 'Вес не может превышать 500 кг'
        }
    )
    
    blood_pressure = forms.CharField(
        max_length=10,
        required=False,
        label="Артериальное давление",
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        validators=[]
    )
    
    heart_rate = forms.IntegerField(
        min_value=30,
        max_value=300,
        required=False,
        label="Частота сердечных сокращений",
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        error_messages={
            'min_value': 'ЧСС не может быть менее 30 уд/мин',
            'max_value': 'ЧСС не может превышать 300 уд/мин'
        }
    )
    
    temperature = forms.FloatField(
        min_value=30,
        max_value=45,
        initial=36.6,
        required=False,
        label="Температура тела (°C)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        error_messages={
            'min_value': 'Температура не может быть ниже 30°C',
            'max_value': 'Температура не может превышать 45°C'
        }
    )
    
    symptoms = forms.CharField(
        required=False,
        label="Симптомы",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        max_length=1000
    )
    
    diagnosis = forms.CharField(
        max_length=200,
        required=False,
        label="Диагноз",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    def clean_patient_name(self):
        patient_name = self.cleaned_data['patient_name'].strip()
        if not patient_name:
            raise ValidationError('Имя пациента не может быть пустым')
        if len(patient_name) < 2:
            raise ValidationError('Имя пациента должно содержать минимум 2 символа')
        return patient_name
    
    def clean_blood_pressure(self):
        blood_pressure = self.cleaned_data['blood_pressure'].strip()
        if blood_pressure:
            if '/' not in blood_pressure:
                raise ValidationError('Давление должно быть в формате: верхнее/нижнее (например: 120/80)')
            parts = blood_pressure.split('/')
            if len(parts) != 2:
                raise ValidationError('Давление должно быть в формате: верхнее/нижнее')
            try:
                systolic = int(parts[0])
                diastolic = int(parts[1])
                if systolic < 60 or systolic > 250:
                    raise ValidationError('Верхнее давление должно быть от 60 до 250')
                if diastolic < 40 or diastolic > 150:
                    raise ValidationError('Нижнее давление должно быть от 40 до 150')
                if systolic <= diastolic:
                    raise ValidationError('Верхнее давление должно быть больше нижнего')
            except ValueError:
                raise ValidationError('Давление должно содержать только числа')
        return blood_pressure
    
    def clean_heart_rate(self):
        heart_rate = self.cleaned_data['heart_rate']
        if heart_rate and (heart_rate < 30 or heart_rate > 300):
            raise ValidationError('ЧСС должна быть от 30 до 300 уд/мин')
        return heart_rate
    
    def clean_temperature(self):
        temperature = self.cleaned_data['temperature']
        if temperature and (temperature < 30 or temperature > 45):
            raise ValidationError('Температура должна быть от 30 до 45°C')
        return temperature
    
    def clean(self):
        cleaned_data = super().clean()
        height = cleaned_data.get('height')
        weight = cleaned_data.get('weight')
        
        if height and weight:
            bmi = weight / ((height / 100) ** 2)
            if bmi < 10:
                raise ValidationError({'weight': 'ИМТ слишком низкий. Проверьте введенные данные.'})
            if bmi > 80:
                raise ValidationError({'weight': 'ИМТ слишком высокий. Проверьте введенные данные.'})
        
        return cleaned_data

class MedicalRecordEditForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['patient_name', 'age', 'gender', 'height', 'weight', 
                 'blood_pressure', 'heart_rate', 'temperature', 'symptoms', 'diagnosis']
        widgets = {
            'patient_name': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'blood_pressure': forms.TextInput(attrs={'class': 'form-control'}),
            'heart_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'symptoms': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'diagnosis': forms.TextInput(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'patient_name': {'required': 'Введите имя пациента'},
            'age': {'required': 'Введите возраст'},
            'gender': {'required': 'Выберите пол'},
            'height': {'required': 'Введите рост'},
            'weight': {'required': 'Введите вес'},
        }
    
    def clean_patient_name(self):
        patient_name = self.cleaned_data['patient_name'].strip()
        if not patient_name:
            raise ValidationError('Имя пациента не может быть пустым')
        if len(patient_name) < 2:
            raise ValidationError('Имя пациента должно содержать минимум 2 символа')
        return patient_name
    
    def clean_age(self):
        age = self.cleaned_data['age']
        if age < 0 or age > 150:
            raise ValidationError('Возраст должен быть от 0 до 150 лет')
        return age
    
    def clean_height(self):
        height = self.cleaned_data['height']
        if height < 50 or height > 300:
            raise ValidationError('Рост должен быть от 50 до 300 см')
        return height
    
    def clean_weight(self):
        weight = self.cleaned_data['weight']
        if weight < 1 or weight > 500:
            raise ValidationError('Вес должен быть от 1 до 500 кг')
        return weight
    
    def clean_blood_pressure(self):
        blood_pressure = self.cleaned_data['blood_pressure']
        if blood_pressure:
            blood_pressure = blood_pressure.strip()
            if '/' not in blood_pressure:
                raise ValidationError('Давление должно быть в формате: верхнее/нижнее (например: 120/80)')
            parts = blood_pressure.split('/')
            if len(parts) != 2:
                raise ValidationError('Давление должно быть в формате: верхнее/нижнее')
            try:
                systolic = int(parts[0])
                diastolic = int(parts[1])
                if systolic < 60 or systolic > 250:
                    raise ValidationError('Верхнее давление должно быть от 60 до 250')
                if diastolic < 40 or diastolic > 150:
                    raise ValidationError('Нижнее давление должно быть от 40 до 150')
                if systolic <= diastolic:
                    raise ValidationError('Верхнее давление должно быть больше нижнего')
            except ValueError:
                raise ValidationError('Давление должно содержать только числа')
        return blood_pressure
    
    def clean_heart_rate(self):
        heart_rate = self.cleaned_data['heart_rate']
        if heart_rate and (heart_rate < 30 or heart_rate > 300):
            raise ValidationError('ЧСС должна быть от 30 до 300 уд/мин')
        return heart_rate or 0
    
    def clean_temperature(self):
        temperature = self.cleaned_data['temperature']
        if temperature and (temperature < 30 or temperature > 45):
            raise ValidationError('Температура должна быть от 30 до 45°C')
        return temperature or 36.6
    
    def clean(self):
        cleaned_data = super().clean()
        height = cleaned_data.get('height')
        weight = cleaned_data.get('weight')
        
        if height and weight:
            bmi = weight / ((height / 100) ** 2)
            if bmi < 10:
                self.add_error('weight', 'ИМТ слишком низкий. Проверьте введенные данные.')
            elif bmi > 80:
                self.add_error('weight', 'ИМТ слишком высокий. Проверьте введенные данные.')
        
        return cleaned_data

class JSONUploadForm(forms.ModelForm):
    class Meta:
        model = JSONFile
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.json'
            }),
        }
    
    def clean_file(self):
        file = self.cleaned_data['file']
        if file.size > 5 * 1024 * 1024: 
            raise ValidationError("Файл слишком большой. Максимальный размер: 5MB")
        
        if not file.name.lower().endswith('.json'):
            raise ValidationError("Разрешены только файлы с расширением .json")
        
        return file 
