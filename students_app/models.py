from django.db import models
from datetime import datetime

# -----------------
# Student Model
# -----------------
class Student(models.Model):
    GENDER_CHOICES = [('M','Male'), ('F','Female')]
    GRADE_CHOICES = [
        ('Baby Class','Baby Class'), ('PP1','PP1'), ('PP2','PP2'),
        ('Grade 1','Grade 1'), ('Grade 2','Grade 2'), ('Grade 3','Grade 3'),
        ('Grade 4','Grade 4'), ('Grade 5','Grade 5'), ('Grade 6','Grade 6'),
        ('Grade 7','Grade 7'), ('Grade 8','Grade 8'), ('Grade 9','Grade 9')
    ]
    BOARDING_CHOICES = [("Yes","Yes"),("No","No")]

    name = models.CharField(max_length=100)
    admission_number = models.CharField(max_length=20, unique=True)
    student_grade = models.CharField(max_length=20, choices=GRADE_CHOICES)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    is_boarder = models.CharField(max_length=3, choices=BOARDING_CHOICES, default="No")
    date_of_birth = models.DateField(blank=True, null=True)
    admission_year = models.IntegerField(default=datetime.now().year)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    parent_name = models.CharField(max_length=100, blank=True)
    is_alumni = models.BooleanField(default=False)
    year_of_completion = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.admission_number})"


# -----------------
# Term Model
# -----------------
class Term(models.Model):
    name = models.CharField(max_length=20)  # Term 1, Term 2, Term 3
    start_date = models.DateField()
    end_date = models.DateField()
    academic_year = models.IntegerField()

    def __str__(self):
        return f"{self.name} ({self.academic_year})"


# -----------------
# Fee Model
# -----------------
class Fee(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fees')
    term = models.ForeignKey(Term, on_delete=models.CASCADE, blank=True, null=True)  # ⚡ Keep nullable
    payment_year = models.IntegerField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    mpesa_code = models.CharField(max_length=20, blank=True, null=True)
    old_arrears = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        term_name = self.term.name if self.term else "No Term"
        return f"{self.student.name} - {term_name} - Kshs {self.amount_paid}"


# -----------------
# Used Admission Numbers
# -----------------
class UsedAdmissionNumber(models.Model):
    admission_number = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.admission_number
    

    
    def __str__(self):
        return f"{self.name} ({self.admission_number})"
 
class AcademicYear(models.Model):
    name = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return self.name