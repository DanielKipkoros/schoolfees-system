from django.db import models
from students_app.models import Student
from datetime import datetime
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal
from django.db.models import Max, Sum

class AcademicYear(models.Model):
    name = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return self.name    


class Term(models.Model):
    name = models.CharField(max_length=20)  # Term 1, Term 2, Term 3
    start_date = models.DateField()
    end_date = models.DateField()
    academic_year = models.IntegerField()

    def __str__(self):
        return f"{self.name} - {self.academic_year}"


class Fee(models.Model):

    PAYMENT_CHOICES = [
        ("Cash", "Cash"),
        ("Bank", "Bank"),
        ("Mpesa", "Mpesa"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    payment_year = models.IntegerField(default=datetime.now().year, blank=True, null=True)

    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, blank=True, null=True)
    mpesa_code = models.CharField(max_length=20, blank=True, null=True)
    old_arrears = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    payment_date = models.DateField(default=timezone.now)
    receipt = models.FileField(upload_to='receipts/%Y/%m/%d/', null=True, blank=True)
    date_paid = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    academic_year = models.ForeignKey(
    AcademicYear,
    on_delete=models.PROTECT,
    null=True,
    blank=True,
    related_name="fees"
    )
    receipt_number = models.PositiveBigIntegerField(
        unique=True,
        null=True,
        blank=True
    )
    
    

    def __str__(self):
        return f"{self.student} - {self.term} - {self.payment_year} - {self.amount_paid}"


  

    def __str__(self):
        return f"{self.student} - {self.term} - {self.payment_year} - {self.amount_paid}"

@property
def balance(self):
    """
    Calculates balance for this student in this specific term & year.
    """

    from .models import FeeStructure

    # Get correct fee structure
    try:
        structure = FeeStructure.objects.get(
            grade=self.student.student_grade,
            term=self.term.name,
            academic_year=self.payment_year
        )
    except FeeStructure.DoesNotExist:
        return Decimal('0.00')

    term_fee = Decimal(structure.amount)

    if getattr(self.student, 'is_boarder', 'No') == "Yes":
        term_fee += Decimal(structure.boarding_amount)

    # Only payments for same student + same term + same year
    total_paid = Fee.objects.filter(
        student=self.student,
        term=self.term,
        payment_year=self.payment_year
    ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')

    total_balance = Decimal(self.old_arrears or 0) + term_fee - total_paid

    return max(total_balance, Decimal('0.00'))

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
        ('STUDENT_PROMOTE', 'Student Promoted'),
        ('STUDENT_EDITED', 'Student Edited'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=30, choices=ACTION_TYPES)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"


class FeeStructure(models.Model):

    ACADEMIC_TERMS = [
        ('Term 1', 'Term 1'),
        ('Term 2', 'Term 2'),
        ('Term 3', 'Term 3'),
    ]

    # -----------------------------
    # Academic Year Reference ⭐ (Professional Design)
    # -----------------------------
    academic_year = models.ForeignKey(
        "AcademicYear",
        on_delete=models.PROTECT,
        related_name="fee_structures",
        help_text="Academic year for this fee structure"
    )

    # -----------------------------
    # Grade / Class
    # -----------------------------
    grade = models.CharField(
        max_length=50,
        help_text="Class or grade level"
    )

    # -----------------------------
    # Term
    # -----------------------------
    term = models.CharField(
        max_length=10,
        choices=ACADEMIC_TERMS
    )

    # -----------------------------
    # Financial Fields
    # -----------------------------
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    boarding_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # -----------------------------
    # Metadata
    # -----------------------------
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('grade', 'term', 'academic_year')
        ordering = ['academic_year', 'grade', 'term']

    def __str__(self):
        return f"{self.grade} - {self.term} ({self.academic_year})"

class FeeAdjustment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    academic_year = models.PositiveIntegerField()

    status_choices = [
        ("PRESENT", "Present / Billable"),
        ("ABSENT", "Not Present / Exempted"),
        ("CLEARED", "Cleared"),
    ]

    status = models.CharField(max_length=20, choices=status_choices)

    deduction_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(auto_now_add=True)
 