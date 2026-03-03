from django.contrib import admin
from .models import Fee, ActivityLog, Term, FeeStructure, AcademicYear
from students_app.models import Student  # ✅ Import Student from students_app


# -----------------------------
# Register Basic Models
# -----------------------------
admin.site.register(Fee)           
admin.site.register(ActivityLog)   
admin.site.register(Term)
admin.site.register(AcademicYear)   # ✅ THIS WAS MISSING


# -----------------------------
# Fee Structure Admin
# -----------------------------
@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('grade', 'term', 'academic_year', 'amount', 'boarding_amount')
    list_filter = ('grade', 'term', 'academic_year')

    # Dynamically set choices for the grade field in admin form
    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "grade":
            grades = Student.objects.values_list('student_grade', flat=True).distinct()
            kwargs['choices'] = [(g, g) for g in grades if g]
        return super().formfield_for_choice_field(db_field, request, **kwargs)