from django import forms
from .models import Fee
from datetime import datetime

class FeeForm(forms.ModelForm):
    class Meta:
        model = Fee
        fields = [
            "term",
            "payment_year",
            "amount_paid",
            "payment_method",
            "mpesa_code",
            
        ]

        widgets = {
            "term": forms.Select(attrs={"class": "form-select"}),

            # Payment Year dropdown
            "payment_year": forms.Select(
                choices=[(y, y) for y in range(2020, datetime.now().year + 2)],
                attrs={"class": "form-select"}
            ),

            "amount_paid": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter amount"
            }),

            "payment_method": forms.Select(attrs={
                "class": "form-select"
            }),

            "mpesa_code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Mpesa Code"
            }),

            # File input for receipts
            "receipt": forms.ClearableFileInput(attrs={
                "class": "form-control"
            }),
        }
