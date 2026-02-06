from django.urls import path
from . import views

urlpatterns = [
    # Home page
    path('', views.home, name='home'),

    # Student pages
    path('add-student/', views.add_student, name='add_student'),
    path('view-students/', views.view_students, name='view_students'),
    path('edit-student/<str:admission_number>/', views.edit_student, name='edit_student'),
    path('delete-student/<str:admission_number>/', views.delete_student, name='delete_student'),
]
