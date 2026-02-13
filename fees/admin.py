from django.contrib import admin
from .models import Fee, ActivityLog, Term
from students_app.models import Student  # ✅ Import Student from students_app

# Register models

admin.site.register(Fee)           # Fees table
admin.site.register(ActivityLog)   # Logs
admin.site.register(Term)          # Term table
