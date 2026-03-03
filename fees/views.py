import re
import os
from datetime import datetime
from collections import OrderedDict

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.conf import settings
from django.db.models import Sum, Q, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.files import File
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from xhtml2pdf import pisa
from num2words import num2words

# Import models
from students_app.models import Student, UsedAdmissionNumber, Term
from fees.models import Fee, ActivityLog
# Import forms
from students_app.forms import StudentForm
from fees.forms import FeeForm
from decimal import Decimal
from django.urls import reverse
import tempfile
from weasyprint import HTML
from django.db.models import Max, Sum
from io import BytesIO
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.db.models import F
from .models import Fee, FeeStructure

import base64
from django.templatetags.static import static
from django.contrib.staticfiles import finders
from fees.models import AcademicYear
from .models import FeeAdjustment
from django.http import JsonResponse
from django.views.decorators.http import require_POST

logo_path = finders.find('students_app/images/pass.png')
with open(logo_path, 'rb') as f:
    logo_data = f.read()
logo_base64 = base64.b64encode(logo_data).decode('utf-8')
logo_data_url = f'data:image/png;base64,{logo_base64}'






@login_required 
def add_fee(request):
    """
    Add a fee payment for a student.
    - Automatically bills the student based on the term, grade & year using FeeStructure.
    - Saves the actual amount paid entered in the form.
    - Handles boarders and old arrears.
    - Generates a unique receipt number immediately.
    """
    if request.method == "POST":
        form = FeeForm(request.POST, request.FILES)

        if form.is_valid():
            fee = form.save(commit=False)

            # Ensure payment year is set
            if not fee.payment_year:
                fee.payment_year = datetime.now().year

            student = fee.student
            term = fee.term
            grade = student.student_grade
            payment_year = fee.payment_year

            # -----------------------------
            # Get fee structure dynamically
            # -----------------------------
            academic_year_obj = AcademicYear.objects.filter(
             name=str(payment_year)
            ).first()

            structure = FeeStructure.objects.filter(
             grade=grade,
             term=term.name,
             academic_year=academic_year_obj
            ).first()            

            if structure:
                term_fee = Decimal(structure.amount)
                if getattr(student, "is_boarder", "No") == "Yes":
                    term_fee += Decimal(structure.boarding_amount)
            else:
                term_fee = Decimal('0.00')
                messages.warning(
                    request,
                    f"⚠ Fee structure not found for {grade}, {term.name}, {payment_year}. Defaulting amount due to Ksh {term_fee}."
                )

            fee.amount_due = term_fee  # Store full due amount for this term

            # Use the amount_paid entered in the form
            fee.amount_paid = Decimal(fee.amount_paid or '0.00')

            # Save the fee first
            fee.save()

            # -----------------------------
            # 🔥 Generate new receipt number immediately
            # -----------------------------
            if not fee.receipt_number:
                last_number = Fee.objects.aggregate(max_no=Max('receipt_number'))['max_no']
                fee.receipt_number = (last_number + 1) if last_number else 1001
                fee.save(update_fields=['receipt_number'])

            messages.success(
                request,
                f"✅ Payment recorded for {student.name}. "
                f"Amount Paid: Ksh {fee.amount_paid}. "
                f"Amount Due: Ksh {term_fee}. Receipt Number: {fee.receipt_number}"
            )

            # Redirect to add another fee if needed
            if request.POST.get('action') == 'add_another':
                return redirect('add_fee')

            # Redirect to list_fees filtered for this student
            return redirect(
                f"{reverse('list_fees')}?search={student.name}&grade={grade}&year={payment_year}&term={term.id}"
            )

        else:
            print(form.errors)
            messages.error(request, "❌ Please correct the errors below.")

    else:
        form = FeeForm()

    return render(request, 'fees/add_fee.html', {'form': form})



@login_required
def list_fees(request):
    search_query = request.GET.get('search', '').strip()
    grade_filter = request.GET.get('grade', '').strip()
    year_filter = request.GET.get('year', '').strip()
    term_raw = request.GET.get('term', '').strip()

    try:
        term_filter = int(term_raw)
    except (ValueError, TypeError):
        term_filter = None

    fees_qs = Fee.objects.select_related('student', 'term')

    if term_filter:
        fees_qs = fees_qs.filter(term_id=term_filter)

    if grade_filter:
        fees_qs = fees_qs.filter(student__student_grade=grade_filter)

    if year_filter:
        fees_qs = fees_qs.filter(payment_year=year_filter)

    if search_query:
        fees_qs = fees_qs.filter(
            Q(student__name__icontains=search_query) |
            Q(student__admission_number__icontains=search_query)
        )

    fee_list = []

    # ⭐ Safe model loading for attendance adjustment
    from django.apps import apps
    FeeAdjustmentModel = apps.get_model('fees', 'FeeAdjustment')

    for fee in fees_qs:

        student = fee.student

        # ⭐ ALUMNI LOGIC
        if student.is_alumni:

            total_paid = Fee.objects.filter(
                student=student
            ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')

            total_arrears = Fee.objects.filter(
                student=student
            ).aggregate(total=Sum('old_arrears'))['total'] or Decimal('0')

            dynamic_balance = total_arrears - total_paid

            fee_list.append({
                'admission_number': student.admission_number,
                'name': student.name,
                'grade': "ALUMNI",
                'term_name': "ALUMNI",
                'payment_year': fee.payment_year,
                'total_paid': total_paid,
                'old_arrears': total_arrears,
                'dynamic_balance': dynamic_balance,
                'is_alumni': True,
                'fee_id': fee.id,
                'has_receipt': bool(fee.receipt),
            })

        # ⭐ NORMAL STUDENTS
        else:

            grade = student.student_grade
            term_name = fee.term.name if fee.term else "N/A"
            year = fee.payment_year

            structure = FeeStructure.objects.filter(
                grade=grade,
                term=term_name,
                academic_year__name=str(year)
            ).first()

            if structure:
                term_fee = Decimal(structure.amount)

                if student.is_boarder == "Yes":
                    term_fee += Decimal(structure.boarding_amount)

            else:
                term_fee = Decimal("0.00")

            total_paid = Decimal(fee.amount_paid or 0)
            old_arrears = Decimal(fee.old_arrears or 0)

            # ⭐ Attendance / Clearance Deduction Logic
            deduction = Decimal("0.00")

            adj = FeeAdjustmentModel.objects.filter(
                student=student,
                term=fee.term,
                academic_year=fee.payment_year
            ).first()

            if adj:
                if adj.status == "ABSENT":
                    deduction = term_fee + old_arrears   # Remove full billing
                elif adj.status == "CLEARED":
                    deduction = Decimal("0.00")
                else:
                    deduction = Decimal(adj.deduction_amount or 0)

            balance = max(
                Decimal("0.00"),
                (term_fee + old_arrears) - total_paid - deduction
            )

            fee_list.append({
                'admission_number': student.admission_number,
                'name': student.name,
                'grade': grade,
                'term_name': term_name,
                'payment_year': year,
                'total_paid': total_paid,
                'old_arrears': old_arrears,
                'dynamic_balance': balance,
                'is_alumni': False,
                'fee_id': fee.id,
                'has_receipt': bool(fee.receipt),
            })

    outstanding = [f for f in fee_list if f['dynamic_balance'] > 0]

    years = Fee.objects.values_list('payment_year', flat=True).distinct()
    terms = Term.objects.all().order_by('start_date')
    grades = list(
        FeeStructure.objects.values_list('grade', flat=True)
        .distinct()
        .order_by('grade')
    )

    today = timezone.localdate()

    current_term = Term.objects.filter(
        start_date__lte=today,
        end_date__gte=today
    ).first()

    return render(request, 'fees/list_fees.html', {
        'fees': fee_list,
        'fees_with_balance': outstanding,
        'search_query': search_query,
        'selected_grade': grade_filter,
        'selected_year': year_filter,
        'selected_term': term_filter,
        'grades': grades,
        'years': years,
        'terms': terms,
        'current_term': current_term.name if current_term else None,
    })
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
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse([], safe=False)

    students = Student.objects.filter(admission_number__icontains=query)[:10]

    results = []
    for s in students:
        results.append({
            "id": s.id,
            "admission": s.admission_number,
            "name": s.name,
            "grade": s.student_grade  # Matches your model field
        })

    return JsonResponse(results, safe=False)

@login_required
def fee_receipt(request, fee_id):
    """
    View a single fee receipt.
    - Shows current payment and term balances.
    - Supports print mode via ?print=1
    """

    fee = get_object_or_404(Fee, id=fee_id)
    student = fee.student
    print_mode = request.GET.get('print') == '1'

    # -----------------------------
    # All fees for this student
    # -----------------------------
    student_fees = (
        Fee.objects
        .filter(student=student)
        .select_related('term')
        .values(
            'payment_year',
            'term__name',
            'term__id',
            'student__is_boarder'
        )
        .annotate(
            total_paid=Sum('amount_paid'),
            total_old_arrears=Sum('old_arrears')
        )
        .order_by('payment_year', 'term__id')
    )

    term_balances = OrderedDict()
    carry_forward = Decimal('0.00')

    # 🔥 Load FeeAdjustment model safely
    from django.apps import apps
    FeeAdjustmentModel = apps.get_model('fees', 'FeeAdjustment')

    for f in student_fees:

        year = f['payment_year']
        term_name = f['term__name'] if f['term__name'] else "N/A"

        # ✅ Fee Structure Lookup
        structure = FeeStructure.objects.filter(
            grade=student.student_grade,
            term=term_name,
            academic_year__name=str(year)
        ).first()

        if structure:
            term_fee = Decimal(structure.amount)

            if student.is_boarder == "Yes":
                term_fee += Decimal(structure.boarding_amount)
        else:
            term_fee = Decimal('0.00')

        old_arrears = Decimal(f['total_old_arrears'] or 0)
        paid = Decimal(f['total_paid'] or 0)

        # ⭐ Attendance / Adjustment deduction
        deduction = Decimal('0.00')

        adj = FeeAdjustmentModel.objects.filter(
            student=student,
            term__name=term_name,
            academic_year=year
        ).first()

        if adj:
            if adj.status == "ABSENT":
                deduction = term_fee + old_arrears
            elif adj.status == "CLEARED":
                deduction = old_arrears
            else:
                deduction = Decimal(adj.deduction_amount or 0)

        # Carry forward + balance logic
        total_due = term_fee + old_arrears - carry_forward
        balance = total_due - paid - deduction

        if balance < 0:
            carry_forward = -balance
            balance = Decimal('0.00')
        else:
            carry_forward = Decimal('0.00')

        if year not in term_balances:
            term_balances[year] = {}

        term_balances[year][term_name] = {
            'fee': term_fee,
            'old_arrears': old_arrears,
            'paid': paid,
            'balance': max(balance, Decimal('0.00')),
            'carry_forward': carry_forward,
        }

    context = {
        'fee': fee,
        'student': student,
        'term_balances': term_balances,
        'print_mode': print_mode,
        'current_payment_amount': fee.amount_paid,
        'receipt_no': fee.receipt_number,
        'school_name': 'ST JOSEPH PREPARATORY SCHOOL',
        'logo_url': logo_data_url,
    }

    return render(request, 'fees/receipt.html', context)
   
# ----------------------------------
# Generate PDF Receipt (Display + Save Offline)
# ----------------------------------


@login_required
def generate_receipt(request, fee_id):
    try:
        with transaction.atomic():
            fee = get_object_or_404(Fee.objects.select_for_update(), id=fee_id)

            # ------------------------------
            # Generate receipt number if missing
            # ------------------------------
            if not fee.receipt_number:
                last_number = Fee.objects.aggregate(max_no=Max('receipt_number'))['max_no']
                fee.receipt_number = (last_number + 1) if last_number else 1001
                fee.save(update_fields=['receipt_number'])

            # ------------------------------
            # Get Fee Structure
            # ------------------------------
            term_name = fee.term.name if fee.term else "N/A"

            structure = FeeStructure.objects.filter(
                grade=fee.student.student_grade,
                term=term_name,
                academic_year__name=str(fee.payment_year)
            ).first()

            if structure:
                term_fee = Decimal(structure.amount)
                if fee.student.is_boarder == "Yes":
                    term_fee += Decimal(structure.boarding_amount)
            else:
                term_fee = Decimal('0.00')

            # ------------------------------
            # Compute total paid and balance with adjustment
            # ------------------------------
            total_paid = Fee.objects.filter(
                student=fee.student,
                payment_year=fee.payment_year,
                term=fee.term
            ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')

            # 🔹 Apply FeeAdjustment if exists
            from django.apps import apps
            FeeAdjustmentModel = apps.get_model('fees', 'FeeAdjustment')

            deduction = Decimal('0.00')
            adj = FeeAdjustmentModel.objects.filter(
                student=fee.student,
                term=fee.term,
                academic_year=fee.payment_year
            ).first()

            if adj:
                if adj.status == "ABSENT":
                    deduction = term_fee + Decimal(fee.old_arrears or 0)
                elif adj.status == "CLEARED":
                    deduction = Decimal(fee.old_arrears or 0)
                else:
                    deduction = Decimal(adj.deduction_amount or 0)

            balance = max(Decimal('0.00'), (term_fee + Decimal(fee.old_arrears or 0)) - total_paid - deduction)

            # Amount in words
            amount_in_words = num2words(fee.amount_paid, to='currency', lang='en').capitalize()

            # ------------------------------
            # Prepare logo URL
            # ------------------------------
            logo_url = logo_data_url

            # ------------------------------
            # Render HTML template
            # ------------------------------
            html_string = render_to_string('fees/receipt.html', {
                'fee': fee,
                'receipt_no': fee.receipt_number,
                'total_fee': term_fee,
                'amount_in_words': amount_in_words,
                'balance': balance,
                'current_payment_amount': fee.amount_paid,
                'school_name': 'ST JOSEPH PREPARATORY SCHOOL',
                'logo_url': logo_url,
                'term_balances': {},
                'term_data': {'balance': balance},
            })

            # ------------------------------
            # Generate PDF
            # ------------------------------
            pdf_buffer = BytesIO()
            HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(pdf_buffer)
            pdf_buffer.seek(0)

            pdf_filename = f"receipt_{fee.receipt_number}.pdf"

            # Save PDF to media
            fee.receipt.save(pdf_filename, ContentFile(pdf_buffer.getvalue()), save=True)

            # Log activity
            ActivityLog.objects.create(
                user=request.user,
                action='RECEIPT_GENERATED',
                description=f"Generated receipt {fee.receipt_number} for {fee.student.name} "
                            f"(Adm: {fee.student.admission_number})"
            )

            # Return PDF in browser
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{pdf_filename}"'
            return response

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        messages.error(request, f"Error generating receipt: {e}")
        return redirect('fee_receipt', fee_id=fee_id)

# -------------------------------
# Download PDF Receipt
# -------------------------------
@login_required
def download_receipt(request, fee_id):
    fee = get_object_or_404(Fee, id=fee_id)

    # 🔥 Get FeeStructure dynamically
    structure = FeeStructure.objects.filter(
        grade=fee.student.student_grade,
        term=fee.term.name,
        academic_year__name=str(fee.payment_year)
    ).first()

    if structure:
        term_fee = Decimal(structure.amount)
        if fee.student.is_boarder == "Yes":
            term_fee += Decimal(structure.boarding_amount)
    else:
        term_fee = Decimal('0.00')

    total_paid = Fee.objects.filter(
        student=fee.student,
        payment_year=fee.payment_year,
        term=fee.term
    ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')

    # 🔹 Apply FeeAdjustment if exists
    from django.apps import apps
    FeeAdjustmentModel = apps.get_model('fees', 'FeeAdjustment')

    deduction = Decimal('0.00')
    adj = FeeAdjustmentModel.objects.filter(
        student=fee.student,
        term=fee.term,
        academic_year=fee.payment_year
    ).first()

    if adj:
        if adj.status == "ABSENT":
            deduction = term_fee + Decimal(fee.old_arrears or 0)
        elif adj.status == "CLEARED":
            deduction = Decimal(fee.old_arrears or 0)
        else:
            deduction = Decimal(adj.deduction_amount or 0)

    balance = max(Decimal('0.00'), (term_fee + Decimal(fee.old_arrears or 0)) - total_paid - deduction)

    amount_in_words = num2words(fee.amount_paid, to='currency', lang='en').capitalize()

    html_string = render_to_string('fees/receipt.html', {
        'fee': fee,
        'total_fee': term_fee,
        'amount_in_words': amount_in_words,
        'balance': balance,
        'receipt_no': fee.receipt_number,
        'school_name': 'ST JOSEPH PREPARATORY SCHOOL',
        'logo_url': logo_data_url,
        'download': True,
    })

    pdf = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{fee.receipt_number}.pdf"'

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

# ----------------------------------
# Redo / Reverse Payment
# ----------------------------------
@staff_member_required
def redo_payment(request, fee_id):
    fee = get_object_or_404(Fee, id=fee_id)

    student_name = fee.student.name
    admission = fee.student.admission_number
    amount = fee.amount_paid

    # Delete receipt file if it exists
    if fee.receipt:
        if os.path.isfile(fee.receipt.path):
            os.remove(fee.receipt.path)

    # Log action BEFORE deleting
    ActivityLog.objects.create(
        user=request.user,
        action="PAYMENT_REVERSED",
        description=f"Reversed payment of Kshs {amount} for {student_name} (Adm: {admission}) - Term {fee.term.name} {fee.payment_year}"
    )

    # Delete payment record
    fee.delete()

    messages.success(request, f"✅ Payment of Kshs {amount} reversed successfully.")

    return redirect('list_fees')



@login_required
def receipt_list(request):
    search_query = request.GET.get('search', '').strip()
    selected_grade = request.GET.get('grade', '')
    selected_year = request.GET.get('year', '')
    selected_term = request.GET.get('term', '')

    # Start with all Fee objects that have a receipt
    receipts = Fee.objects.select_related('student', 'term').filter(receipt_number__isnull=False)

    # Filter by search query (name, admission number, receipt number)
    if search_query:
        receipts = receipts.filter(
            Q(student__name__icontains=search_query) |
            Q(student__admission_number__icontains=search_query) |
            Q(receipt_number__icontains=search_query)
        )

    # Filter by grade
    if selected_grade:
        receipts = receipts.filter(student__student_grade=selected_grade)

    # Filter by payment year
    if selected_year:
        receipts = receipts.filter(payment_year=selected_year)

    # Filter by term
    if selected_term:
        receipts = receipts.filter(term__id=selected_term)

    # Order by latest payment date first, then by ID to break ties
    receipts = receipts.order_by('-payment_date', '-id')

    # Get all distinct grades and years for filters
    grades = Fee.objects.values_list('student__student_grade', flat=True).distinct()
    years = Fee.objects.values_list('payment_year', flat=True).distinct()

    context = {
        'receipts': receipts,
        'search_query': search_query,
        'selected_grade': selected_grade,
        'selected_year': selected_year,
        'selected_term': selected_term,
        'grades': grades,
        'years': years,
       
    }
    return render(request, 'fees/receipt_list.html', context)


@login_required
@staff_member_required
def mark_fee_adjustment(request, fee_id, status):
    fee = get_object_or_404(Fee, id=fee_id)

    # Save adjustment log
    FeeAdjustment.objects.create(
        student=fee.student,
        term=fee.term,
        academic_year=fee.payment_year,
        status=status
    )

    # Get fee structure
    structure = FeeStructure.objects.filter(
        grade=fee.student.student_grade,
        term=fee.term.name,
        academic_year__name=str(fee.payment_year)
    ).first()

    term_fee = Decimal("0.00")

    if structure:
        term_fee = Decimal(structure.amount)

        if fee.student.is_boarder == "Yes":
            term_fee += Decimal(structure.boarding_amount)

    # ⭐ ABSENT = Exempt billing (Set amount_due to 0)
    if status == "ABSENT":
        fee.amount_due = Decimal("0.00")

        # Do NOT add arrears
        fee.old_arrears = Decimal("0.00")

    # ⭐ CLEARED = Reset arrears
    elif status == "CLEARED":
        fee.old_arrears = Decimal("0.00")

    # ⭐ PRESENT = Normal billing
    else:
        fee.amount_due = term_fee

    fee.save()

    messages.success(request, f"Fee marked as {status}")
    return redirect("list_fees")