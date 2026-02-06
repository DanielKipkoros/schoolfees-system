from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.add_fee, name='add_fee'),
    path('list/', views.list_fees, name='list_fees'),
    path('get-student-info/', views.get_student_info, name='get_student_info'),
    path('search-students/', views.search_students, name='search_students'),
    path('receipt/view/<int:fee_id>/', views.fee_receipt, name='fee_receipt'),
    path('receipt/generate/<int:fee_id>/', views.generate_receipt, name='generate_receipt'),
]