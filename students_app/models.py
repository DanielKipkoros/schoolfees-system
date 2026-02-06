from django.db import models
from datetime import datetime

class Student(models.Model):
    # -----------------
    # Choices
    # -----------------
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    GRADE_CHOICES = [
        ('Baby Class', 'Baby Class'),
        ('PP1', 'PP1'),
        ('PP2', 'PP2'),
        ('Grade 1', 'Grade 1'),
        ('Grade 2', 'Grade 2'),
        ('Grade 3', 'Grade 3'),
        ('Grade 4', 'Grade 4'),
        ('Grade 5', 'Grade 5'),
        ('Grade 6', 'Grade 6'),
        ('Grade 7', 'Grade 7'),
        ('Grade 8', 'Grade 8'),
        ('Grade 9', 'Grade 9'),
    ]

    BOARDING_CHOICES = [
        ("Yes", "Yes"),
        ("No", "No"),
    ]

    # -----------------
    # Fields
    # -----------------
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

    # -----------------
    # Methods
    # -----------------
    def __str__(self):
        return f"{self.name} ({self.admission_number})"

    @property
    def total_fee_per_term(self):
        """
        Returns a dictionary of fees per year and per term for this student.
        Can be used to calculate balances starting from admission_year.
        """
        fees = {
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
            },
        }

        # Return only fees for this student's grade
        student_fees = {year: fees[year].get(self.student_grade, {}) for year in fees if year >= self.admission_year}
        return student_fees
