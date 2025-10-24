from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_medical_record, name='create_record'),
    path('upload/', views.upload_json_file, name='upload_json'),
    path('files/', views.view_json_files, name='view_json_files'),
    path('records/', views.view_medical_records, name='view_records'),
    path('search/', views.search_records, name='search_records'),
    path('edit/<uuid:record_id>/', views.edit_record, name='edit_record'),
    path('delete/<uuid:record_id>/', views.delete_record, name='delete_record'),
]
