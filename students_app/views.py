from django.shortcuts import render, redirect, get_object_or_404
from .models import Student
from .forms import StudentForm
from django.db.models import Q
from django.contrib import messages 

# Home page


def home(request):
    return render(request, 'students_app/home.html')

# Add a new student
def add_student(request):
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save()  # Save to database

            # Show success message
            messages.success(request, f"✅ Student recorded: {student.name}")

            # Determine which button was clicked
            action = request.POST.get('action')
            if action == 'add_another':
                # Clear the form to add another student
                form = StudentForm()
            else:
                # Redirect to student list after normal "Save Student"
                return redirect('view_students')
        else:
            # Form invalid: show errors
            messages.error(request, "❌ Please correct the errors below.")
            # Django will automatically display field errors in template
    else:
        form = StudentForm()

    return render(request, "students_app/add_student.html", {
        "form": form
    })
def view_students(request):
    search_query = request.GET.get('search', '')
    selected_grade = request.GET.get('grade', '')
    selected_year = request.GET.get('admission_year', '')

    students = Student.objects.all()

    # Search filter: name OR admission_number
    if search_query:
        students = students.filter(
            Q(name__icontains=search_query) | Q(admission_number__icontains=search_query)
        )

    # Grade filter
    if selected_grade:
        students = students.filter(student_grade=selected_grade)

    # Admission year filter
    if selected_year:
        students = students.filter(admission_year=selected_year)

    # Get all unique grades for dropdown
    classes = Student.objects.values_list('student_grade', flat=True).distinct()

    # Get all unique admission years for dropdown
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
# Edit a student
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

# Delete a student
def delete_student(request, admission_number):
    student = get_object_or_404(Student, admission_number=admission_number)
    if request.method == 'POST':
        student.delete()
        return redirect('view_students')
    return render(request, 'students_app/delete_student.html', {'student': student})
    
