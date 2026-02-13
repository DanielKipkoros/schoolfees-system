import re
import os
import json
from datetime import datetime, date
from decimal import Decimal
from collections import OrderedDict

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.conf import settings
from django.db.models import Sum, Q, F, DecimalField, Count
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.files import File
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from xhtml2pdf import pisa
from num2words import num2words

from .models import Fee, Term, ActivityLog
from .forms import FeeForm
from students_app.models import Student, UsedAdmissionNumber
from students_app.forms import StudentForm









# -------------------------
# Current year fee structure
# -------------------------
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

BOARDING_FEE = 8000  # Additional fee for boarders

@login_required
def add_student(request):
    # -------------------------
    # Get last used admission number
    # -------------------------
    last_used = UsedAdmissionNumber.objects.order_by('-id').first()
    last_admission_number = last_used.admission_number if last_used else "None Yet"

    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            admission_number = form.cleaned_data['admission_number']

            # Check if this admission number was already used
            if UsedAdmissionNumber.objects.filter(admission_number=admission_number).exists():
                messages.error(request, f"❌ Admission Number {admission_number} has already been used.")
            else:
                # Save student
                student = form.save()

                # Log student creation
                ActivityLog.objects.create(
                    user=request.user,
                    action='STUDENT_CREATE',
                    description=f"Added student {student.name} (Adm: {student.admission_number})"
                )

                # Save admission number to UsedAdmissionNumber
                UsedAdmissionNumber.objects.create(admission_number=admission_number)

                messages.success(request, f"✅ Student recorded: {student.name}")

                # Reset form if "Add Another" is clicked
                action = request.POST.get('action')
                if action == 'add_another':
                    form = StudentForm()
                else:
                    return redirect('view_students')
        else:
            messages.error(request, "❌ Please correct the errors below.")
    else:
        form = StudentForm()

    context = {
        "form": form,
        "last_admission_number": last_admission_number,  # Pass to template
    }
    return render(request, "students_app/add_student.html", context)
# ----------------------------------
# List Fees with Generated column
# ----------------------------------
@login_required
def list_fees(request):
    search_query = request.GET.get('search', '').strip()
    grade_filter = request.GET.get('grade', '').strip()
    year_filter = request.GET.get('year', '').strip()
    term = request.GET.get('term', '').strip()

    fees = Fee.objects.select_related('student', 'term').all().order_by('-id')

    if search_query:
        fees = fees.filter(
            Q(student__name__icontains=search_query) |
            Q(student__admission_number__icontains=search_query)
        )

    if grade_filter:
        fees = fees.filter(student__student_grade=grade_filter)

    if year_filter:
        fees = fees.filter(payment_year=year_filter)

    if term:
        fees = fees.filter(term_id=term)  # properly indented

    # -----------------------------
    # Compute dynamic balances
    # -----------------------------
    fee_list = []
    for fee in fees:
        term_fee = CURRENT_YEAR_FEES.get(fee.student.student_grade, {}).get(fee.term.name, 0)
        if getattr(fee.student, 'is_boarder', 'No') == "Yes":
            term_fee += BOARDING_FEE

        paid_so_far = Fee.objects.filter(
            student=fee.student,
            payment_year=fee.payment_year,
            term=fee.term
        ).aggregate(total_paid=Sum('amount_paid'))['total_paid'] or 0

        fee.dynamic_balance = float(fee.old_arrears or 0) + float(term_fee) - float(paid_so_far)
        fee.receipt_generated = bool(fee.receipt)

        fee_list.append(fee)

    # -----------------------------
    # Students with outstanding balances (current term only)
    # -----------------------------
    CURRENT_TERM = "Term 1"
    student_balances = OrderedDict()
    for fee in fee_list:
        if fee.term.name != CURRENT_TERM:
            continue
        if fee.dynamic_balance > 0:
            if search_query and search_query.lower() not in fee.student.name.lower() and search_query not in fee.student.admission_number:
                continue
            if grade_filter and fee.student.student_grade != grade_filter:
                continue
            if year_filter and str(fee.payment_year) != str(year_filter):
                continue

            student_id = fee.student.id
            if student_id not in student_balances or fee.id > student_balances[student_id].id:
                student_balances[student_id] = fee

    fees_with_balance = list(student_balances.values())
    years = Fee.objects.order_by('payment_year').values_list('payment_year', flat=True).distinct()

    # -----------------------------
    # ADD THIS: Get all terms for the dropdown
    # -----------------------------
    terms = Term.objects.all().order_by('name')

    context = {
        'fees': fee_list,
        'fees_with_balance': fees_with_balance,
        'search_query': search_query,
        'selected_grade': grade_filter,
        'selected_year': year_filter,
        'grades': list(CURRENT_YEAR_FEES.keys()),
        'years': years,
        'terms': terms,  # now defined
    }

    return render(request, 'fees/list_fees.html', context)



# ----------------------------------
# Get student info (AJAX)
# ----------------------------------
@login_required
def get_student_info(request):
    admission_number = request.GET.get('admission_number')
    try:
        student = Student.objects.get(admission_number=admission_number)
        data = {
            'name': student.name,
            'grade': student.student_grade,
            'is_boarder': student.is_boarder,
        }
    except Student.DoesNotExist:
        data = {'error': 'Student not found'}
    return JsonResponse(data)

# ----------------------------------
# Search students (autocomplete)
# ----------------------------------
@login_required
def search_students(request):
    q = request.GET.get("q", "")
    students = Student.objects.filter(admission_number__icontains=q)[:10]
    results = []
    for s in students:
        results.append({
            "id": s.id,
            "admission": s.admission_number,
            "name": s.name,
            "grade": s.student_grade
        })
    return JsonResponse(results, safe=False)

# -------------------------------
# Fee Receipt (HTML)
# -------------------------------
@login_required
def fee_receipt(request, fee_id, download=False):
    fee = get_object_or_404(Fee, id=fee_id)

    # Use .term.name here as well
    term_fee = CURRENT_YEAR_FEES.get(fee.student.student_grade, {}).get(fee.term.name, 0)

    if getattr(fee.student, 'is_boarder', 'No') == "Yes":
        term_fee += BOARDING_FEE

    total_paid = Fee.objects.filter(
        student=fee.student,
        payment_year=fee.payment_year,
        term=fee.term
    ).aggregate(total=Sum('amount_paid'))['total'] or 0

    balance = float(fee.old_arrears or 0) + float(term_fee) - float(total_paid)

    context = {
        'fee': fee,
        'total_fee': term_fee,
        'total_paid': total_paid,
        'balance': balance,
        'amount_in_words': num2words(fee.amount_paid, to='currency', lang='en'),
        'school_name': 'ST JOSEPH PREPARATORY SCHOOL',
        'logo_url': request.build_absolute_uri(static('students_app/images/pass.png')),
        'download': download,
    }
    return render(request, 'fees/receipt.html', context)



# ----------------------------------
# Generate PDF Receipt
# ----------------------------------
@login_required
def generate_receipt(request, fee_id):
    try:
        fee = get_object_or_404(Fee, id=fee_id)

        # Correct term lookup
        term_fee = CURRENT_YEAR_FEES.get(fee.student.student_grade, {}).get(fee.term.name, 0)
        if getattr(fee.student, 'is_boarder', 'No') == "Yes":
            term_fee += BOARDING_FEE

        # Total amount paid so far for this term
        total_paid = Fee.objects.filter(
            student=fee.student,
            payment_year=fee.payment_year,
            term=fee.term
        ).aggregate(total=Sum('amount_paid'))['total'] or 0

        balance = float(fee.old_arrears or 0) + float(term_fee) - float(total_paid)

        amount_in_words = num2words(fee.amount_paid, to='currency', lang='en').capitalize()

        html = render_to_string('fees/receipt.html', {
            'fee': fee,
            'total_fee': term_fee,
            'amount_in_words': amount_in_words,
            'balance': balance,
            'school_name': 'ST JOSEPH PREPARATORY SCHOOL'
        })

        if not os.path.exists(settings.MEDIA_ROOT):
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        temp_pdf_path = os.path.join(settings.MEDIA_ROOT, f"temp_receipt_{fee.id}.pdf")

        # Generate PDF
        with open(temp_pdf_path, "wb") as f:
            result = pisa.CreatePDF(src=html, dest=f)
            if result.err:
                messages.error(request, "Error generating PDF. Check your template HTML.")
                return redirect('fee_receipt', fee_id=fee.id)

        # Save PDF to Fee model
        with open(temp_pdf_path, "rb") as f:
            django_file = File(f)
            pdf_filename = f"receipt_{fee.id}.pdf"
            fee.receipt.save(pdf_filename, django_file, save=True)

        # Log receipt generation
        ActivityLog.objects.create(
            user=request.user,
            action='RECEIPT_GENERATE',
            description=f"Generated receipt for {fee.student.name} (Adm: {fee.student.admission_number}), Amount: Kshs {fee.amount_paid}"
        )

        # Remove temp file
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

        # Return PDF in browser
        with open(fee.receipt.path, "rb") as f:
            response = HttpResponse(f.read(), content_type="application/pdf")
            response['Content-Disposition'] = f'inline; filename="{pdf_filename}"'
            return response

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        messages.error(request, f"An error occurred while generating the receipt: {e}")
        print(f"[DEBUG generate_receipt]\n{tb}")
        return redirect('fee_receipt', fee_id=fee_id)



# -------------------------------
# Download PDF Receipt
# -------------------------------
@login_required
def download_receipt(request, fee_id):
    fee = get_object_or_404(Fee, id=fee_id)

    # Correct term lookup
    term_fee = CURRENT_YEAR_FEES.get(fee.student.student_grade, {}).get(fee.term.name, 0)
    if getattr(fee.student, 'is_boarder', 'No') == "Yes":
        term_fee += BOARDING_FEE

    total_paid = Fee.objects.filter(
        student=fee.student,
        payment_year=fee.payment_year,
        term=fee.term
    ).aggregate(total=Sum('amount_paid'))['total'] or 0

    balance = float(fee.old_arrears or 0) + float(term_fee) - float(total_paid)

    amount_in_words = num2words(fee.amount_paid, to='currency', lang='en').capitalize()

    html = render_to_string('fees/receipt.html', {
        'fee': fee,
        'total_fee': term_fee,
        'amount_in_words': amount_in_words,
        'balance': balance,
        'school_name': 'ST JOSEPH PREPARATORY SCHOOL',
        'logo_url': request.build_absolute_uri(static('students_app/images/pass.png')),
        'download': True  # hides download button
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{fee.id}.pdf"'

    pisa_status = pisa.CreatePDF(src=html, dest=response)
    if pisa_status.err:
        return HttpResponse("Error generating PDF. Please check template.")

    return response

@staff_member_required
def dashboard(request):
    # ----------------------------
    # Filters
    # ----------------------------
    search_query = request.GET.get('search', '')
    grade_search = request.GET.get('grade', '')

    students = Student.objects.all()

    if search_query:
        students = students.filter(
            Q(name__icontains=search_query) |
            Q(parent_name__icontains=search_query) |
            Q(admission_number__icontains=search_query)
        )

    if grade_search:
        students = students.filter(student_grade=grade_search)

    # ----------------------------
    # Today's date
    # ----------------------------
    today = timezone.localdate()

    # Payments today
    payments_today = Fee.objects.filter(payment_date=today)
    total_payments_today = payments_today.aggregate(
        total=Coalesce(Sum('amount_paid'), 0, output_field=DecimalField())
    )['total']

    # ----------------------------
    # Total students (current)
    # ----------------------------
    total_students = students.count()

    # ----------------------------
    # Total fees collected (all time)
    # ----------------------------
    # Include fees even if the student was deleted
    total_fees_collected = Fee.objects.aggregate(
        total=Coalesce(Sum('amount_paid'), 0, output_field=DecimalField())
    )['total']

    # Total number of payments
    total_payments_count = Fee.objects.count()

    # ----------------------------
    # Total outstanding arrears
    # ----------------------------
    all_fees = Fee.objects.all()
    total_arrears = 0
    student_arrears = []

    for fee in all_fees:
        # Determine balance
        balance = getattr(fee, 'dynamic_balance', None)
        if balance is None:
            balance = fee.old_arrears or 0

        total_arrears += balance

        # Handle deleted students
        student_name = fee.student.name if fee.student else "Deleted Student"
        student_arrears.append({
            'student': student_name,
            'balance': balance
        })

    # ----------------------------
    # Context for template
    # ----------------------------
    context = {
        'students': students,
        'payments_today': payments_today,
        'total_payments_today': total_payments_today,
        'total_students': total_students,
        'total_fees_collected': total_fees_collected,
        'total_payments_count': total_payments_count,
        'total_arrears': total_arrears,
        'student_arrears': student_arrears,
        'school_name': "ST JOSEPH PREPARATORY SCHOOL",
        
    }

    return render(request, 'fees/dashboard.html', context)

@staff_member_required
def activity_logs(request):
    logs = ActivityLog.objects.all().order_by('-timestamp')
    return render(request, 'fees/activity_logs.html', {'logs': logs})


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ActivityLog.objects.create(
        user=user,
        action="Logged in"
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    ActivityLog.objects.create(
        user=user,
        action="Logged out"
    )

@login_required
def add_fee(request):
    """
    Add a new fee payment for a student.
    """
    if request.method == "POST":
        form = FeeForm(request.POST)
        if form.is_valid():
            fee = form.save(commit=False)

            # Ensure payment_year defaults to current year if not provided
            if not fee.payment_year:
                fee.payment_year = datetime.now().year

            fee.save()

            # Log the fee addition
            ActivityLog.objects.create(
                user=request.user,
                action='FEE_CREATE',
                description=f"Added fee for {fee.student.name} (Adm: {fee.student.admission_number}), Amount: Kshs {fee.amount_paid}"
            )

            messages.success(request, f"✅ Fee for {fee.student.name} recorded successfully.")

            # Check if user clicked "Add Another"
            if request.POST.get('action') == 'add_another':
                form = FeeForm()
            else:
                return redirect('list_fees')
        else:
            messages.error(request, "❌ Please correct the errors below.")
    else:
        form = FeeForm()

    return render(request, 'fees/add_fee.html', {'form': form})