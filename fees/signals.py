from django.db.models.signals import post_save
from django.dispatch import receiver
from students_app.models import Student
from .models import Fee, Term
from datetime import datetime

@receiver(post_save, sender=Student)
def create_fees_for_new_student(sender, instance, created, **kwargs):
    """
    Automatically create Fee records for a new student
    for all terms in the current academic year.
    """
    if created:
        # Get all terms for the current year
        current_year = datetime.now().year
        terms = Term.objects.filter(academic_year=current_year)

        # Loop through terms and create fee records
        for term in terms:
            Fee.objects.create(
                student=instance,
                term=term,
                payment_year=current_year,
                amount_paid=0,
                old_arrears=getattr(instance, "old_arrears", 0),
                payment_method="Cash",  # Default, can be updated later
            )
