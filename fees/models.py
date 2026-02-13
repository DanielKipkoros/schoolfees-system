from django.db import models
from students_app.models import Student
from datetime import datetime
from django.utils import timezone
from django.contrib.auth.models import User

class Term(models.Model):
    name = models.CharField(max_length=20)  # Term 1, Term 2, Term 3
    start_date = models.DateField()
    end_date = models.DateField()
    academic_year = models.IntegerField()

    def __str__(self):
        return f"{self.name} - {self.academic_year}"


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

    CURRENT_YEAR_FEES = {
        'Baby Class': {'Term 1':11700, 'Term 2': 11700, 'Term 3': 11100},
        'PP1': {'Term 1':11700, 'Term 2': 11700, 'Term 3': 11100},
        'PP2': {'Term 1':11700, 'Term 2': 11700, 'Term 3': 11100},
        'Grade 1': {'Term 1': 12750, 'Term 2': 12750, 'Term 3': 12400},
        'Grade 2': {'Term 1': 12750, 'Term 2': 12750, 'Term 3': 12400},
        'Grade 3': {'Term 1': 12750, 'Term 2': 12750, 'Term 3': 12400},
        'Grade 4': {'Term 1': 12750, 'Term 2': 12750, 'Term 3': 12400},
        'Grade 5': {'Term 1': 12750, 'Term 2': 12750, 'Term 3': 12400},
        'Grade 6': {'Term 1': 12750, 'Term 2': 12750, 'Term 3': 12400},
        'Grade 7': {'Term 1': 13900, 'Term 2': 13900, 'Term 3': 13500},
        'Grade 8': {'Term 1': 13900, 'Term 2': 13900, 'Term 3': 13500},
        'Grade 9': {'Term 1': 13900, 'Term 2': 13900, 'Term 3': 13500},
    }

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    payment_year = models.IntegerField(default=datetime.now().year)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, blank=True, null=True)
    mpesa_code = models.CharField(max_length=20, blank=True, null=True)
    old_arrears = models.FloatField(default=0)
    payment_date = models.DateField(default=timezone.now)
    receipt = models.FileField(upload_to='receipts/%Y/%m/%d/', null=True, blank=True)
    date_paid = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.term} - {self.payment_year} - {self.amount_paid}"

    @property
    def balance(self):
        """
        Calculates the balance for this student and term:
        balance = fee for this term + old arrears - sum of all payments made
        """
        student_grade = getattr(self.student, "grade", None)
        if not student_grade:
            return 0

        # Get the fee for this student's grade and term
        term_fee = self.CURRENT_YEAR_FEES.get(student_grade, {}).get(self.term.name, 0)

        # Sum all payments the student has made
        total_paid = Fee.objects.filter(student=self.student).aggregate(
            total=models.Sum("amount_paid")
        )["total"] or 0

        # Add old arrears
        total_balance = term_fee + (self.old_arrears or 0) - float(total_paid)
        return max(total_balance, 0)

    @property
    def is_generated(self):
        return bool(self.receipt and self.receipt.name and self.receipt.storage.exists(self.receipt.name))


class ActivityLog(models.Model):
    ACTION_TYPES = [
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('PAYMENT_CREATE', 'Payment Created'),
        ('PAYMENT_UPDATE', 'Payment Updated'),
        ('PAYMENT_DELETE', 'Payment Deleted'),
        ('STUDENT_CREATE', 'Student Created'),
        ('STUDENT_UPDATE', 'Student Updated'),
        ('STUDENT_DELETE', 'Student Deleted'),
        ('RECEIPT_GENERATE', 'Receipt Generated'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=30, choices=ACTION_TYPES)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"
