from django.contrib import admin
from .models import ReturnRequest,CustomerSupport,LaptopBrand,Laptop,CustomBuildRequest,Payment,Review
from django.utils import timezone
import openpyxl
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.http import HttpResponse
import csv

class LaptopAdmin(admin.ModelAdmin):
    fields = ['brand', 'ram', 'processor', 'display','gpu', 'storage', 'price', ]
    search_fields = ('brand','model',)

admin.site.register(Laptop, LaptopAdmin)
admin.site.register(LaptopBrand)

@admin.register(CustomBuildRequest)
class CustomBuildRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'ram', 'cpu', 'is_possible', 'estimated_price']
    list_filter = ['is_possible']
    search_fields = ['user__username', 'cpu', 'gpu']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'amount', 'method', 'delivery_method',
        'is_successful', 'order_status', 'paid_at'
    )
    list_filter = ('is_successful', 'delivery_method', 'order_status')
    search_fields = ('user__username', 'laptop__model')
    actions = [
        'export_as_excel', 'export_as_pdf',
        'mark_as_approved', 'mark_as_confirmed',
        'mark_as_shipped', 'mark_as_out_for_delivery',
        'mark_as_delivered'
    ]

    def mark_as_approved(self, request, queryset):
        queryset.update(is_approved=True, approved_at=timezone.now())
    mark_as_approved.short_description = "Mark selected payments as Approved"

    def mark_as_confirmed(self, request, queryset):
        queryset.update(order_status='confirmed')
    mark_as_confirmed.short_description = "Mark selected orders as Confirmed"

    def mark_as_shipped(self, request, queryset):
        queryset.update(order_status='shipped')
    mark_as_shipped.short_description = "Mark selected orders as Shipped"

    def mark_as_out_for_delivery(self, request, queryset):
        queryset.update(order_status='out_for_delivery')
    mark_as_out_for_delivery.short_description = "Mark selected orders as Out for Delivery"

    def mark_as_delivered(self, request, queryset):
        queryset.update(order_status='delivered')
    mark_as_delivered.short_description = "Mark selected orders as Delivered"

    def export_as_excel(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="payments.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'User', 'Laptop', 'Amount', 'Method', 'Delivery Method',
            'Order Status', 'Successful', 'Approved', 'Paid At'
        ])

        for payment in queryset:
            writer.writerow([
                payment.user.username,
                payment.laptop.model if payment.laptop else "None",
                payment.amount,
                payment.method,
                payment.delivery_method,
                payment.get_order_status_display(),
                'Yes' if payment.is_successful else 'No',
                'Yes' if payment.is_approved else 'No',
                payment.paid_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        return response
    export_as_excel.short_description = "Export selected as Excel"

    def export_as_pdf(self, request, queryset):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="payments.pdf"'
        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter
        y = height - 40
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Payment Records")
        y -= 25
        p.setFont("Helvetica", 9)

        for payment in queryset:
            line = f"{payment.user.username} | {payment.laptop.model if payment.laptop else 'None'} | " \
                   f"₹{payment.amount} | {payment.method}/{payment.delivery_method} | " \
                   f"{payment.get_order_status_display()} | " \
                   f"{'✔' if payment.is_successful else '✘'} | " \
                   f"{'✔' if payment.is_approved else '✘'} | " \
                   f"{payment.paid_at.strftime('%Y-%m-%d')}"
            p.drawString(50, y, line)
            y -= 18
            if y <= 40:
                p.showPage()
                y = height - 40
        p.save()
        return response
    export_as_pdf.short_description = "Export selected as PDF"

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'laptop', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']

class CustomerSupportAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'created_at', 'responded_at']
    search_fields = ['user__username', 'complaint']
    readonly_fields = ['user', 'phone', 'complaint', 'created_at']
    fields = ['user', 'phone', 'complaint', 'response', 'created_at', 'responded_at']

    def save_model(self, request, obj, form, change):
        if obj.response and not obj.responded_at:
            from django.utils.timezone import now
            obj.responded_at = now()
        super().save_model(request, obj, form, change)

admin.site.register(CustomerSupport, CustomerSupportAdmin)
@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'order', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['user__username', 'order__id']
    readonly_fields = ['user', 'order', 'reason', 'created_at']