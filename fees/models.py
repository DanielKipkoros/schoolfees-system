from django.db import models
from students_app.models import Student
from datetime import datetime

class Fee(models.Model):
    TERM_CHOICES = [
        ("Term 1", "Term 1"),
        ("Term 2", "Term 2"),
        ("Term 3", "Term 3"),
    ]
    PAYMENT_CHOICES = [
        ("Cash", "Cash"),
        ("Bank", "Bank"),
        ("Mpesa", "Mpesa"),
    ]

    # Current grade totals (latest year)
    GRADE_TOTALS = {
        'Baby Class': {'Term 1': 4300, 'Term 2': 3800, 'Term 3': 4500},
        'PP1': {'Term 1': 4400, 'Term 2': 3900, 'Term 3': 4600},
        'PP2': {'Term 1': 4400, 'Term 2': 3900, 'Term 3': 4600},
        'Grade 1': {'Term 1': 5300, 'Term 2': 4800, 'Term 3': 5100},
        'Grade 2': {'Term 1': 5100, 'Term 2': 4700, 'Term 3': 5100},
        'Grade 3': {'Term 1': 6300, 'Term 2': 5800, 'Term 3': 6500},
        'Grade 4': {'Term 1': 7300, 'Term 2': 6800, 'Term 3': 7300},
        'Grade 5': {'Term 1': 7800, 'Term 2': 7300, 'Term 3': 7800},
        'Grade 6': {'Term 1': 8300, 'Term 2': 7800, 'Term 3': 8500},
        'Grade 7': {'Term 1': 8300, 'Term 2': 7800, 'Term 3': 8500},
        'Grade 8': {'Term 1': 8300, 'Term 2': 7800, 'Term 3': 8500},
        'Grade 9': {'Term 1': 8300, 'Term 2': 7800, 'Term 3': 8500},
    }

    # Historical fees: estimates per grade per term for 2022–2025
    HISTORICAL_FEES = {
        2022: {
            'Baby Class': {'Term 1': 4000, 'Term 2': 3500, 'Term 3': 4200},
            'PP1': {'Term 1': 4100, 'Term 2': 3600, 'Term 3': 4300},
            'PP2': {'Term 1': 4100, 'Term 2': 3600, 'Term 3': 4300},
            'Grade 1': {'Term 1': 5000, 'Term 2': 4500, 'Term 3': 4750},
            'Grade 2': {'Term 1': 4800, 'Term 2': 4400, 'Term 3': 4800},
            'Grade 3': {'Term 1': 6000, 'Term 2': 5500, 'Term 3': 6200},
            'Grade 4': {'Term 1': 7000, 'Term 2': 6500, 'Term 3': 7000},
            'Grade 5': {'Term 1': 7500, 'Term 2': 7000, 'Term 3': 7500},
            'Grade 6': {'Term 1': 8000, 'Term 2': 7500, 'Term 3': 8200},
            'Grade 7': {'Term 1': 8000, 'Term 2': 7500, 'Term 3': 8200},
            'Grade 8': {'Term 1': 8000, 'Term 2': 7500, 'Term 3': 8200},
            'Grade 9': {'Term 1': 8000, 'Term 2': 7500, 'Term 3': 8200},
        },
        2023: {
            'Baby Class': {'Term 1': 4100, 'Term 2': 3600, 'Term 3': 4300},
            'PP1': {'Term 1': 4200, 'Term 2': 3700, 'Term 3': 4400},
            'PP2': {'Term 1': 4200, 'Term 2': 3700, 'Term 3': 4400},
            'Grade 1': {'Term 1': 5100, 'Term 2': 4600, 'Term 3': 4850},
            'Grade 2': {'Term 1': 4900, 'Term 2': 4500, 'Term 3': 4900},
            'Grade 3': {'Term 1': 6100, 'Term 2': 5600, 'Term 3': 6300},
            'Grade 4': {'Term 1': 7100, 'Term 2': 6600, 'Term 3': 7100},
            'Grade 5': {'Term 1': 7600, 'Term 2': 7100, 'Term 3': 7600},
            'Grade 6': {'Term 1': 8100, 'Term 2': 7600, 'Term 3': 8300},
            'Grade 7': {'Term 1': 8100, 'Term 2': 7600, 'Term 3': 8300},
            'Grade 8': {'Term 1': 8100, 'Term 2': 7600, 'Term 3': 8300},
            'Grade 9': {'Term 1': 8100, 'Term 2': 7600, 'Term 3': 8300},
        },
        2024: {
            'Baby Class': {'Term 1': 4200, 'Term 2': 3700, 'Term 3': 4400},
            'PP1': {'Term 1': 4300, 'Term 2': 3800, 'Term 3': 4500},
            'PP2': {'Term 1': 4300, 'Term 2': 3800, 'Term 3': 4500},
            'Grade 1': {'Term 1': 5200, 'Term 2': 4700, 'Term 3': 5000},
            'Grade 2': {'Term 1': 5000, 'Term 2': 4600, 'Term 3': 5000},
            'Grade 3': {'Term 1': 6200, 'Term 2': 5700, 'Term 3': 6400},
            'Grade 4': {'Term 1': 7200, 'Term 2': 6700, 'Term 3': 7200},
            'Grade 5': {'Term 1': 7700, 'Term 2': 7200, 'Term 3': 7700},
            'Grade 6': {'Term 1': 8200, 'Term 2': 7700, 'Term 3': 8400},
            'Grade 7': {'Term 1': 8200, 'Term 2': 7700, 'Term 3': 8400},
            'Grade 8': {'Term 1': 8200, 'Term 2': 7700, 'Term 3': 8400},
            'Grade 9': {'Term 1': 8200, 'Term 2': 7700, 'Term 3': 8400},
        },
        2025: {
            'Baby Class': {'Term 1': 4300, 'Term 2': 3800, 'Term 3': 4500},
            'PP1': {'Term 1': 4400, 'Term 2': 3900, 'Term 3': 4600},
            'PP2': {'Term 1': 4400, 'Term 2': 3900, 'Term 3': 4600},
            'Grade 1': {'Term 1': 5300, 'Term 2': 4800, 'Term 3': 5100},
            'Grade 2': {'Term 1': 5100, 'Term 2': 4700, 'Term 3': 5100},
            'Grade 3': {'Term 1': 6300, 'Term 2': 5800, 'Term 3': 6500},
            'Grade 4': {'Term 1': 7300, 'Term 2': 6800, 'Term 3': 7300},
            'Grade 5': {'Term 1': 7800, 'Term 2': 7300, 'Term 3': 7800},
            'Grade 6': {'Term 1': 8300, 'Term 2': 7800, 'Term 3': 8500},
            'Grade 7': {'Term 1': 8300, 'Term 2': 7800, 'Term 3': 8500},
            'Grade 8': {'Term 1': 8300, 'Term 2': 7800, 'Term 3': 8500},
            'Grade 9': {'Term 1': 8300, 'Term 2': 7800, 'Term 3': 8500},
        }
    }

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    term = models.CharField(max_length=10, choices=TERM_CHOICES, default="Term 1")
    payment_year = models.IntegerField(default=datetime.now().year)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES)
    mpesa_code = models.CharField(max_length=20, blank=True, null=True)

    # File upload for receipts
    receipt = models.FileField(upload_to='receipts/%Y/%m/%d/', null=True, blank=True)
    date_paid = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.term} - {self.payment_year} - {self.amount_paid}"

    @property
    def balance(self):
        """
        Calculates remaining balance including arrears from previous years,
        only counting fees since the student's admission year.
        """
        total_due = 0
        admission_year = self.student.admission_year  # make sure Student has this field

        for year in sorted(self.HISTORICAL_FEES.keys()):
            if year < admission_year:
                continue  # skip years before admission
            if year > self.payment_year:
                break  # skip future years

            year_fees = self.HISTORICAL_FEES[year]
            student_fees = year_fees.get(self.student.grade, {})

            for term_name in ["Term 1", "Term 2", "Term 3"]:
                # Only include up to the current term for the current year
                if year == self.payment_year and term_name > self.term:
                    break
                total_due += student_fees.get(term_name, 0)

        # Sum all payments made by this student
        payments = Fee.objects.filter(student=self.student).aggregate(
            total_paid=models.Sum('amount_paid')
        )['total_paid'] or 0

        return max(total_due - float(payments), 0)
