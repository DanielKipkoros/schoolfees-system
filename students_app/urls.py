from django.urls import path
from . import views

urlpatterns = [
    # Home page
    path('', views.home, name='home'),

    # Student management
    path('add-student/', views.add_student, name='add_student'),
    path('view-students/', views.view_students, name='view_students'),
    path('edit-student/<str:admission_number>/', views.edit_student, name='edit_student'),
    path('delete-student/<str:admission_number>/', views.delete_student, name='delete_student'),
    path('promote_students/', views.promote_students, name='promote_students'),
    path('redo_promotion/', views.redo_promotion, name='redo_promotion'),
    path('alumni/', views.alumni_list, name='alumni_list'),

    # Optional: you can add more student-related pages later
    # path('some-other-page/', views.some_other_view, name='some_other'),
]
