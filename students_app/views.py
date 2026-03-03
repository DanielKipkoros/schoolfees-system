from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Sum
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required  # <-- MUST ADD

from .models import Student, Term
from .forms import StudentForm
from fees.models import Fee, ActivityLog
from django.utils import timezone



# -------------------------------
# HOME PAGE
# -------------------------------
@login_required
def home(request):
    return render(request, 'students_app/home.html')


# -------------------------------
# ADD STUDENT
# -------------------------------
@login_required
def add_student(request):
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save()

            # Log the student creation
            ActivityLog.objects.create(
                user=request.user,
                action='STUDENT_CREATE',
                description=f"Added student {student.name} (Adm: {student.admission_number})"
            )

            # Automatically create fee entries for current year terms
            current_year = datetime.now().year
            terms = Term.objects.filter(academic_year=current_year)
            for term in terms:
                Fee.objects.create(
                    student=student,
                    term=term,
                    payment_year=current_year,
                    amount_paid=0,
                    old_arrears=500,  # registration fee
                    payment_method='Pending'
                )

            messages.success(request, f"✅ Student {student.name} added successfully.")
            return redirect('view_students')
        else:
            messages.error(request, "❌ Please correct the errors below.")
    else:
        form = StudentForm()

    return render(request, 'students_app/add_student.html', {'form': form})


# -------------------------------
# VIEW STUDENTS
# -------------------------------
@login_required
def view_students(request):
    search_query = request.GET.get('search', '')
    selected_grade = request.GET.get('grade', '')
    selected_year = request.GET.get('admission_year', '')
    status_filter = request.GET.get('status', '')

    students = Student.objects.all()

    if status_filter == 'active':
        students = students.filter(is_alumni=False)

    elif status_filter == 'alumni':
        students = students.filter(is_alumni=True)

    if search_query:
        students = students.filter(
            Q(name__icontains=search_query) |
            Q(admission_number__icontains=search_query)
        )

    if selected_grade:
        students = students.filter(student_grade=selected_grade)

    if selected_year:
        students = students.filter(admission_year=selected_year)

    classes = Student.objects.values_list('student_grade', flat=True).distinct()
    years = Student.objects.values_list('admission_year', flat=True).distinct().order_by('-admission_year')

    return render(request, 'students_app/view_students.html', {
        'students': students,
        'search_query': search_query,
        'selected_grade': selected_grade,
        'selected_year': selected_year,
        'status_filter': status_filter,
        'classes': classes,
        'years': years,
    })


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

              # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='STUDENT_EDITED',
                description=f"Student Edited {student.name} (Adm: {student.admission_number})"
            )


            messages.success(request, f"✅ Student {student.name} updated successfully.")
            return redirect('view_students')
    else:
        form = StudentForm(instance=student)
    return render(request, 'students_app/edit_student.html', {'form': form, 'student': student})


# -------------------------------
# DELETE STUDENT
# -------------------------------
@login_required
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
        total_paid = Fee.objects.filter(student=student).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
        total_fee = getattr(student, 'total_fee', 0)  # safe fallback
        arrears = total_fee - total_paid
        student_data.append({
            'student': student,
            'total_paid': total_paid,
            'arrears': arrears,
        })

    context = {'student_data': student_data}
    return render(request, 'fees/dashboard.html', context)


@login_required
@staff_member_required
def promote_students(request):

    current_year = datetime.now().year
    next_year = current_year + 1

    grade_map = {
        'Baby Class': 'PP1',
        'PP1': 'PP2',
        'PP2': 'Grade 1',
        'Grade 1': 'Grade 2',
        'Grade 2': 'Grade 3',
        'Grade 3': 'Grade 4',
        'Grade 4': 'Grade 5',
        'Grade 5': 'Grade 6',
        'Grade 6': 'Grade 7',
        'Grade 7': 'Grade 8',
        'Grade 8': 'Grade 9',
        'Grade 9': 'Alumni',
    }

    promoted_count = 0
    alumni_count = 0

    for student in Student.objects.filter(is_alumni=False):

        if student.student_grade in grade_map:

            old_grade = student.student_grade
            new_grade = grade_map[old_grade]

            # Move to alumni
            if new_grade == "Alumni":
                student.is_alumni = True
                student.last_grade = old_grade
                student.year_of_completion = current_year
                alumni_count += 1

            else:
                student.student_grade = new_grade
                promoted_count += 1

                # Create fees for next year (IMPORTANT)
                next_terms = Term.objects.filter(academic_year=next_year)

                for term in next_terms:
                    Fee.objects.create(
                        student=student,
                        term=term,
                        payment_year=next_year,
                        amount_paid=0,
                        old_arrears=0,
                        payment_method="Pending",
                        is_active=True
                    )

            student.save()

            ActivityLog.objects.create(
                user=request.user,
                action="STUDENT_PROMOTE",
                description=f"Promoted {student.name} from {old_grade} to {new_grade}"
            )

    messages.success(
        request,
        f"✅ Promotion complete: {promoted_count} promoted, {alumni_count} moved to alumni."
    )

    return redirect('home')
    
@login_required
@staff_member_required
def redo_promotion(request):

    current_year = datetime.now().year
    next_year = current_year + 1

    last_log = ActivityLog.objects.filter(
        action="STUDENT_PROMOTE"
    ).order_by('-timestamp').first()

    if not last_log:
        messages.error(request, "No promotion records found.")
        return redirect('home')

    # Find students promoted in that log
    promoted_names = re.findall(r'Promoted (.+?) from', last_log.description)

    reverse_map = {
        'PP1': 'Baby Class',
        'PP2': 'PP1',
        'Grade 1': 'PP2',
        'Grade 2': 'Grade 1',
        'Grade 3': 'Grade 2',
        'Grade 4': 'Grade 3',
        'Grade 5': 'Grade 4',
        'Grade 6': 'Grade 5',
        'Grade 7': 'Grade 6',
        'Grade 8': 'Grade 7',
        'Grade 9': 'Grade 8',
    }

    for name in promoted_names:

        try:
            student = Student.objects.get(name=name)

            if student.last_grade:
                student.student_grade = student.last_grade
                student.is_alumni = False
                student.save()

            # ⭐ Restore fees (VERY IMPORTANT PART)
            Fee.objects.filter(
                student=student,
                payment_year=next_year,
                is_active=True
            ).update(is_active=False)

        except Student.DoesNotExist:
            continue

    last_log.delete()

    messages.success(request, "✅ Promotion successfully undone with fees restored.")
    return redirect('home')
    
@login_required
def alumni_list(request):
    alumni = Student.objects.filter(is_alumni=True)

    return render(request, 'students/alumni_list.html', {
        'alumni': alumni
    })

