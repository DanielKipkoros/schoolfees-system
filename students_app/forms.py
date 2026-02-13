from django import forms
from .models import Student
from datetime import datetime

class StudentForm(forms.ModelForm):
    # Define admission_year explicitly as a form field
    admission_year = forms.IntegerField(
        label="Admission Year",
        initial=datetime.now().year,
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'min': 2000,
                'max': datetime.now().year
            }
        )
    )

    class Meta:
        model = Student
        fields = [
            'name',
            'admission_number',
            'student_grade',
            'gender',
            'is_boarder',
            'date_of_birth',
            'admission_year',
            'phone_number',
            'email',
            'parent_name',
        ]
        widgets = {
            'student_grade': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'is_boarder': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'parent_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
