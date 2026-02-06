from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.conf import settings

from .forms import FeeForm
from .models import Fee
from students_app.models import Student

from django.db.models import Sum, Q
from datetime import datetime
from num2words import num2words
from xhtml2pdf import pisa

import math
import os

# ----------------------------------
# Add Fee
# ----------------------------------
def add_fee(request):
    if request.method == "POST":
        admission_number = request.POST.get("admission_number")

        # Get student
        try:
            student = Student.objects.get(admission_number=admission_number)
        except Student.DoesNotExist:
            messages.error(request, "Invalid student admission number.")
            return redirect('add_fee')

        form = FeeForm(request.POST, request.FILES)
        if form.is_valid():
            fee = form.save(commit=False)
            fee.student = student

            if fee.payment_method != "Mpesa":
                fee.mpesa_code = None

            fee.save()

            messages.success(request, f"Fee recorded for {student.name}.")

            # Check which button was clicked
            action = request.POST.get('action')
            if action == 'add_another':
                # Stay on the same page for adding another fee
                return redirect('add_fee')
            else:
                # Normal save: go to fees list
                return redirect('list_fees')

        else:
            messages.error(request, "Please correct the errors below.")

    else:
        form = FeeForm()

    current_year = datetime.now().year
    years = list(range(current_year - 10, current_year + 2))

    return render(request, 'fees/add_fee.html', {
        'form': form,
        'years': years
    })

# ----------------------------------
# List Fees
# ----------------------------------
def list_fees(request):
    search_query = request.GET.get('search', '').strip()
    grade_filter = request.GET.get('grade', '').strip()
    year_filter = request.GET.get('year', '').strip()

    fees = Fee.objects.select_related('student').all().order_by('-date_paid')

    # Search filter
    if search_query:
        fees = fees.filter(
            Q(student__name__icontains=search_query) |
            Q(student__admission_number__icontains=search_query)
        )

    # Grade filter
    if grade_filter:
        fees = fees.filter(student__student_grade=grade_filter)

    # Year filter
    if year_filter:
        fees = fees.filter(payment_year=year_filter)

    # Fee structure
    grade_totals = {
        'Baby Class': 11700,
        'PP1': 11700,
        'PP2': 11700,
        'Grade 1': 12750,
        'Grade 2': 12000,
        'Grade 3': 15000,
        'Grade 4': 18000,
        'Grade 5': 20000,
        'Grade 6': 22000,
        'Grade 7': 22000,
        'Grade 8': 22000,
        'Grade 9': 22000,
    }

    # Calculate balances
    fee_list = []
    for fee in fees:
        total_fee = grade_totals.get(fee.student.student_grade, 10000)
        paid_so_far = Fee.objects.filter(
            student=fee.student,
            payment_year=fee.payment_year,
            student__student_grade=fee.student.student_grade
        ).aggregate(total_paid=Sum('amount_paid'))['total_paid'] or 0

        fee.dynamic_balance = float(total_fee) - float(paid_so_far)
        fee_list.append(fee)

    # Totals per grade
    totals_by_grade = fees.values(
        'student__student_grade'
    ).annotate(total_amount=Sum('amount_paid'))

    # Years
    years = Fee.objects.order_by('payment_year').values_list('payment_year', flat=True).distinct()

    context = {
        'fees': fee_list,
        'search_query': search_query,
        'selected_grade': grade_filter,
        'selected_year': year_filter,
        'grades': list(grade_totals.keys()),
        'years': years,
        'totals_by_grade': totals_by_grade,
    }

    return render(request, 'fees/list_fees.html', context)


# ----------------------------------
# Get student info
# ----------------------------------
def get_student_info(request):
    admission_number = request.GET.get('admission_number')
    try:
        student = Student.objects.get(admission_number=admission_number)
        data = {
            'name': student.name,
            'grade': student.student_grade,
        }
    except Student.DoesNotExist:
        data = {'error': 'Student not found'}
    return JsonResponse(data)


# ----------------------------------
# Search students
# ----------------------------------
def search_students(request):
    q = request.GET.get('q', '')
    students = Student.objects.filter(admission_number__icontains=q)
    results = [
        {
            'admission': s.admission_number,
            'name': s.name,
            'grade': s.student_grade
        } for s in students
    ]
    return JsonResponse(results, safe=False)


# ----------------------------------
# Convert number to words
# ----------------------------------
def number_to_words(amount):
    units = [
        "Zero","One","Two","Three","Four","Five","Six",
        "Seven","Eight","Nine","Ten","Eleven","Twelve",
        "Thirteen","Fourteen","Fifteen","Sixteen",
        "Seventeen","Eighteen","Nineteen"
    ]
    tens = ["","","Twenty","Thirty","Forty","Fifty","Sixty","Seventy","Eighty","Ninety"]

    def words(n):
        if n < 20:
            return units[int(n)]
        elif n < 100:
            return tens[int(n//10)] + ('' if n % 10 == 0 else ' ' + units[int(n % 10)])
        elif n < 1000:
            return units[int(n//100)] + ' Hundred' + ('' if n % 100 == 0 else ' ' + words(n % 100))
        elif n < 1000000:
            return words(n//1000) + ' Thousand' + ('' if n % 1000 == 0 else ' ' + words(n % 1000))
        else:
            return str(n)
    return words(math.floor(amount)) + ' Shillings'


# ----------------------------------
# Receipt View
# ----------------------------------
def fee_receipt(request, fee_id):
    fee = get_object_or_404(Fee, id=fee_id)

    total_paid = Fee.objects.filter(
        student=fee.student,
        payment_year=fee.payment_year,
        student__student_grade=fee.student.student_grade
    ).aggregate(total=Sum('amount_paid'))['total'] or 0

    grade_totals = {
        'Baby Class': 11700,
        'PP1': 11700,
        'PP2': 11700,
        'Grade 1': 12750,
        'Grade 2': 12000,
        'Grade 3': 15000,
        'Grade 4': 18000,
        'Grade 5': 20000,
        'Grade 6': 22000,
        'Grade 7': 22000,
        'Grade 8': 22000,
        'Grade 9': 22000,
    }

    total_fee = grade_totals.get(fee.student.student_grade, 10000)
    balance = total_fee - total_paid

    context = {
        'fee': fee,
        'total_fee': total_fee,
        'total_paid': total_paid,
        'balance': balance,
        'amount_in_words': num2words(fee.amount_paid, to='currency', lang='en'),
        'school_name': 'ST JOSEPH PREPARATORY SCHOOL'
    }

    return render(request, 'fees/receipt.html', context)


# ----------------------------------
# Generate PDF Receipt
# ----------------------------------
def generate_receipt(request, fee_id):
    fee = get_object_or_404(Fee, id=fee_id)
    amount_in_words = num2words(fee.amount_paid, to='currency', lang='en').capitalize()

    html = render_to_string('fees/receipt.html', {
        'fee': fee,
        'amount_in_words': amount_in_words
    })

    receipt_dir = os.path.join(settings.MEDIA_ROOT, 'receipts', str(fee.payment_year))
    os.makedirs(receipt_dir, exist_ok=True)
    pdf_filename = f"receipt_{fee.id}.pdf"
    pdf_path = os.path.join(receipt_dir, pdf_filename)

    with open(pdf_path, "wb") as f:
        pisa.CreatePDF(html, dest=f)

    fee.receipt_file.name = f'receipts/{fee.payment_year}/{pdf_filename}'
    fee.save()

    with open(pdf_path, "rb") as f:
        response = HttpResponse(f.read(), content_type="application/pdf")
        response['Content-Disposition'] = f'inline; filename="{pdf_filename}"'
        return response
