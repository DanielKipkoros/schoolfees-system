from django import forms
from .models import Fee
from students_app.models import Student

class FeeForm(forms.ModelForm):
    admission_number = forms.CharField(
        label="Admission Number",
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter admission number",
            "autocomplete": "off"
        })
    )

    student_name = forms.CharField(
        label="Student Name",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "readonly": "readonly"
        })
    )

    student_grade = forms.CharField(
        label="Grade",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "readonly": "readonly"
        })
    )

    class Meta:
        model = Fee
        exclude = ['student', 'receipt', 'date_paid']
        widgets = {
            "term": forms.Select(attrs={"class": "form-select"}),
            "amount_paid": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter amount",
                "step": "0.01",
                "min": "0"
            }),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
            "mpesa_code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Mpesa Code"
            }),
            "old_arrears": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter old fee arrears",
                "step": "0.01",
                "min": "0"
            }),
            "payment_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
        }

    def clean_admission_number(self):
        admission_number = self.cleaned_data.get("admission_number").strip()
        try:
            self.student = Student.objects.get(admission_number=admission_number)
        except Student.DoesNotExist:
            raise forms.ValidationError("Student with this admission number does not exist.")
        return admission_number

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get("payment_method")
        mpesa_code = cleaned_data.get("mpesa_code")

        if payment_method == "Mpesa" and not mpesa_code:
            self.add_error(
                "mpesa_code",
                "MPESA Code is required when payment method is Mpesa."
            )

        return cleaned_data

    def save(self, commit=True):
        fee = super().save(commit=False)

        # Attach the student from clean_admission_number
        fee.student = getattr(self, 'student', None)

        if commit:
            fee.save()

        return fee
