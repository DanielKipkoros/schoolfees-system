from datetime import datetime
import re
from django.shortcuts import render, redirect, get_object_or_404
from .models import Student
from .forms import StudentForm
from fees.models import Fee
from django.db.models import Q, Sum
from django.contrib import messages 
from django.contrib.auth.decorators import login_required
from fees.models import ActivityLog
from .models import Student, UsedAdmissionNumber, Term, Fee



# -------------------------------
# HOME PAGE
# -------------------------------
@login_required
def home(request):
    return render(request, 'students_app/home.html')


@login_required
def add_student(request):
    REGISTRATION_FEE = 500  # KES registration fee

    # -------------------------
    # Get last used admission number
    # -------------------------
    last_used = UsedAdmissionNumber.objects.order_by('-id').first()
    last_admission_number = last_used.admission_number if last_used else None

    # -------------------------
    # Compute next admission number (auto-increment)
    # -------------------------
    if last_admission_number:
        match = re.search(r'(\d+)$', last_admission_number)
        if match:
            numeric_part = int(match.group(1))
            prefix = last_admission_number[:match.start(1)]
            next_adm_number = f"{prefix}{numeric_part + 1}"
        else:
            next_adm_number = f"{last_admission_number}1"
    else:
        next_adm_number = "1"

    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            admission_number = form.cleaned_data.get("admission_number")

            # -------------------------
            # Prevent reuse of admission numbers
            # -------------------------
            if UsedAdmissionNumber.objects.filter(admission_number=admission_number).exists():
                messages.error(request, f"❌ Admission number {admission_number} has already been used.")
            else:
                student = form.save()

                # Log student creation
                ActivityLog.objects.create(
                    user=request.user,
                    action='STUDENT_CREATE',
                    description=f"Added student {student.name} (Adm: {student.admission_number})"
                )

                # Record used admission number
                UsedAdmissionNumber.objects.create(admission_number=student.admission_number)

                # -------------------------
                # Add registration fee as old arrears for each term
                # -------------------------
                current_year = datetime.now().year
                terms = Term.objects.filter(academic_year=current_year)
                for term in terms:
                    Fee.objects.create(
                        student=student,
                        term=term,
                        payment_year=current_year,
                        amount_paid=0,
                        old_arrears=REGISTRATION_FEE,  # registration fee counted here
                        payment_method='Pending'
                    )

                messages.success(
                    request,
                    f"✅ Student recorded: {student.name} with registration fee added to old arrears."
                )

                # Reset form or redirect
                if request.POST.get('action') == 'add_another':
                    form = StudentForm(initial={'admission_number': str(int(next_adm_number) + 1)})
                else:
                    return redirect('view_students')
        else:
            messages.error(request, "❌ Please correct the errors below.")
    else:
        form = StudentForm(initial={'admission_number': next_adm_number})

    context = {
        "form": form,
        "last_admission_number": last_admission_number,
        "next_admission_number": next_adm_number
    }

    return render(request, "students_app/add_student.html", context)
# -------------------------------
# VIEW STUDENTS
# -------------------------------
@login_required
def view_students(request):
    search_query = request.GET.get('search', '')
    selected_grade = request.GET.get('grade', '')
    selected_year = request.GET.get('admission_year', '')

    students = Student.objects.all()
    if search_query:
        students = students.filter(
            Q(name__icontains=search_query) | Q(admission_number__icontains=search_query)
        )
    if selected_grade:
        students = students.filter(student_grade=selected_grade)
    if selected_year:
        students = students.filter(admission_year=selected_year)

    classes = Student.objects.values_list('student_grade', flat=True).distinct()
    years = Student.objects.values_list('admission_year', flat=True).distinct().order_by('-admission_year')

    context = {
        'students': students,
        'search_query': search_query,
        'selected_grade': selected_grade,
        'selected_year': selected_year,
        'classes': classes,
        'years': years,
    }
    return render(request, 'students_app/view_students.html', context)

# -------------------------------
# EDIT STUDENT
# -------------------------------
@login_required
def edit_student(request, admission_number):
    student = get_object_or_404(Student, admission_number=admission_number)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect('view_students')
    else:
        form = StudentForm(instance=student)
    return render(request, 'students_app/edit_student.html', {'form': form, 'student': student})

# -------------------------------
# DELETE STUDENT
# -------------------------------
@login_required  # 🔐 NOW SECURED
def delete_student(request, admission_number):
    student = get_object_or_404(Student, admission_number=admission_number)
    if request.method == 'POST':
        student.delete()

        ActivityLog.objects.create(
    user=request.user,
    action='STUDENT_DELETE',
    description=f"Deleted student {student.name} (Adm: {student.admission_number})"
)

        messages.success(request, f"✅ Student {student.name} deleted")
        return redirect('view_students')
    return render(request, 'students_app/delete_student.html', {'student': student})

# -------------------------------
# DASHBOARD (FEES)
# -------------------------------
@login_required
def dashboard(request):
    students = Student.objects.all()
    student_data = []

    for student in students:
        total_paid = Fee.objects.filter(student=student).aggregate(Sum('amount'))['amount__sum'] or 0
        total_fee = getattr(student, 'total_fee', 0)  # safe fallback
        arrears = total_fee - total_paid
        student_data.append({
            'student': student,
            'total_paid': total_paid,
            'arrears': arrears,
        })

    context = {'student_data': student_data}
    return render(request, 'fees/dashboard.html', context)
