from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import ReturnRequest,CustomerSupport,Laptop,LaptopBrand,Laptop,CartItem, Order,Address,UserProfile,CustomBuildRequest, Payment,Review
from .forms import ReturnRequestForm,CustomerSupportForm,RegisterForm,LaptopForm,AddressForm,CustomBuildForm,UserProfileForm,AddressForm,UserForm,PaymentForm,ReviewForm
from django.conf import settings
from django.shortcuts import get_object_or_404,get_list_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required 
from django.views.decorators.csrf import csrf_exempt
from bapp.models import UserProfile
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.http import HttpResponse
from django.db.models import Count, Sum
from django.utils.timezone import now, timedelta
from django.db.models.functions import TruncDate
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from bapp.sales_predictor import generate_sales_prediction


for user in User.objects.all():
    UserProfile.objects.get_or_create(user=user)

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        uname = request.POST['username']
        pwd = request.POST['password']
        user = authenticate(username=uname, password=pwd)
        if user:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def dashboard_view(request):
    laptops = Laptop.objects.all()
    return render(request, 'dashboard.html', {'laptops': laptops})
@staff_member_required(login_url='login') 
def add_laptop_view(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    if not request.user.is_staff:
        return HttpResponseForbidden("You are not authorized to access this page.")
    if request.method == 'POST':
        form = LaptopForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = LaptopForm()
    return render(request, 'add_laptop.html', {'form': form})

def home_view(request):
    laptops = Laptop.objects.all()

    # General search query
    query = request.GET.get('q')
    if query:
        laptops = laptops.filter(
            Q(brand__icontains=query) |
            Q(model__icontains=query) |
            Q(processor__icontains=query) |
            Q(ram__icontains=query) |
            Q(storage__icontains=query) |
            Q(display__icontains=query) |
            Q(description__icontains=query)
        )

    # Filters
    brand = request.GET.get('brand')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    ram = request.GET.get('ram')

    if brand:
        laptops = laptops.filter(brand__name__icontains=brand)
    if min_price:
        laptops = laptops.filter(price__gte=min_price)
    if max_price:
        laptops = laptops.filter(price__lte=max_price)
    if ram:
        laptops = laptops.filter(ram__icontains=ram)  # ✅ Corrected field

    context = {
        'laptops': laptops,
        'brands': Laptop.objects.values_list('brand', flat=True).distinct(),  # if LaptopBrand model not used
    }
    return render(request, 'home.html', context)

def laptop_detail(request, id):
    laptop = get_object_or_404(Laptop, id=id)
    # Get sort method from request
    sort_option = request.GET.get('sort', 'newest')
    # Sorting logic
    if sort_option == 'highest':
        reviews = Review.objects.filter(laptop=laptop).order_by('-rating')
    elif sort_option == 'lowest':
        reviews = Review.objects.filter(laptop=laptop).order_by('rating')
    elif sort_option == 'oldest':
        reviews = Review.objects.filter(laptop=laptop).order_by('created_at')
    else:  # Default: newest
        reviews = Review.objects.filter(laptop=laptop).order_by('-created_at')
    return render(request, 'laptop_detail.html', {
    'laptop': laptop,
    'reviews': reviews,
    'sort_option': sort_option,})

@login_required
def add_to_cart(request, laptop_id):
    laptop = get_object_or_404(Laptop, id=laptop_id)
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user, 
        laptop=laptop
        )
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('view_cart')

def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, user=request.user)
    item.delete()
    return redirect('view_cart')

@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.laptop.price * item.quantity for item in cart_items)

    # Fetch latest or default address
    address = Address.objects.filter(user=request.user).first()

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total': total,
        'address': address
    })

@login_required
def checkout(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user)

    if not cart_items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('view_cart')
    try:
        address = Address.objects.get(user=user)
    except Address.DoesNotExist:
        address = None
    if request.method == 'POST':
        # Update quantities and deletions
        for item in cart_items:
            quantity = request.POST.get(f'quantity_{item.id}')
            delete = request.POST.get(f'delete_{item.id}')
            if delete:
                item.delete()
            elif quantity and quantity.isdigit() and int(quantity) > 0:
                item.quantity = int(quantity)
                item.save()
        # Refresh cart after updates
        cart_items = CartItem.objects.filter(user=user)
        if not cart_items.exists():
            messages.warning(request, "Your cart is empty after updates.")
            return redirect('view_cart')

        # Handle payment
        delivery_method = request.POST.get('delivery_method')
        card_name = request.POST.get('card_name')
        card_pin = request.POST.get('card_pin')
        pay_cash_option = request.POST.get('cash_option')

        if delivery_method == "Online":
            if not card_name or not card_pin:
                messages.error(request, "Card details required.")
                return render(request, 'checkout.html', locals())
        elif delivery_method == "Cash":
            if not pay_cash_option:
                messages.error(request, "Choose a cash payment option.")
                return render(request, 'checkout.html', locals())

        total_price = sum(item.laptop.price * item.quantity for item in cart_items)

        payment = Payment.objects.create(
            user=user,
            amount=total_price,
            method=delivery_method,
            card_name=card_name if delivery_method == "Online" else '',
            is_successful=True,
            paid_at=timezone.now(),
        )

        cart_items.delete()
        return redirect('payment_success', payment_id=payment.id)

    total_price = sum(item.laptop.price * item.quantity for item in cart_items)
    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'address': address
    })

def laptop_detail(request, id):
    laptop = get_object_or_404(Laptop, id=id)
    return render(request, 'laptop_detail.html', {'laptop': laptop})

@staff_member_required
def edit_laptop_view(request,id):
    laptop=get_object_or_404(Laptop,id=id)
    if request.method=='POST':
        form=LaptopForm(request.POST,request.FILES,instance=laptop)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
        else:
            return render(request, 'edit_laptop.html', {'form': form, 'laptop': laptop})
    else:
            form=LaptopForm(instance=laptop)
            return render(request, 'edit_laptop.html', {'form': form, 'laptop': laptop})

@login_required
def payment_gateway(request, laptop_id):
    laptop = get_object_or_404(Laptop, id=laptop_id)

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.user = request.user
            payment.laptop = laptop
            payment.is_successful = True  # assume successful after validation
            payment.save()
            return redirect('payment_success', payment_id=payment.id)
        else:
            messages.error(request, "Payment failed. Please fill all required fields.")
    else:
        form = PaymentForm()

    return render(request, 'payment_gateway.html', {
        'form': form,
        'laptop': laptop
    })

@login_required

def buy_now(request, laptop_id):
    laptop = get_object_or_404(Laptop, id=laptop_id)
    user = request.user

    # 🔹 Get address of the logged-in user
    try:
        address = Address.objects.get(user=user)
    except Address.DoesNotExist:
        address = None

    if request.method == 'POST':
        delivery_method = request.POST.get('delivery_method')
        card_name = request.POST.get('card_name')
        card_pin = request.POST.get('card_pin')
        pay_cash_option = request.POST.get('cash_option')

        if delivery_method == "Online":
            if not card_name or not card_pin:
                messages.error(request, "Card details required.")
                return render(request, 'buy_now.html', {'laptop': laptop, 'address': address})
        elif delivery_method == "Cash":
            if not pay_cash_option:
                messages.error(request, "Choose a cash payment option.")
                return render(request, 'buy_now.html', {'laptop': laptop, 'address': address})

        payment = Payment.objects.create(
            user=user,
            amount=laptop.price,
            method=delivery_method,
            card_name=card_name if delivery_method == "Online" else '',
            is_successful=True,
            paid_at=timezone.now(),
        )

        return redirect('payment_success', payment_id=payment.id)

    return render(request, 'buy_now.html', {'laptop': laptop, 'address': address})


@csrf_exempt
@login_required
def payment_success(request, payment_id=None):
    payment = None
    if payment_id:
        payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    return render(request, 'payment_success.html', {'payment': payment})

@csrf_exempt
@login_required
def add_or_update_address(request):
    try:
        address = Address.objects.get(user=request.user)
    except Address.DoesNotExist:
        address = None

    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            addr = form.save(commit=False)
            addr.user = request.user
            addr.save()
            return redirect('home')  # Or redirect to checkout/payment
    else:
        form = AddressForm(instance=address)

    return render(request, 'address_form.html', {'form': form})

@login_required
def user_profile(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    payments = Payment.objects.filter(user=user, is_successful=True).order_by('-paid_at')
    custom_builds = CustomBuildRequest.objects.filter(user=user)

    try:
        address = Address.objects.get(user=user)
    except Address.DoesNotExist:
        address = None

    if request.method == 'POST':
        u_form = UserForm(request.POST, instance=user)
        p_form = UserProfileForm(request.POST, instance=profile)
        a_form = AddressForm(request.POST, instance=address)

        if u_form.is_valid() and p_form.is_valid() and a_form.is_valid():
            u_form.save()
            p_form.save()
            addr = a_form.save(commit=False)
            addr.user = user
            addr.save()
            return redirect('user_profile')
    else:
        u_form = UserForm(instance=user)
        p_form = UserProfileForm(instance=profile)
        a_form = AddressForm(instance=address)

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'a_form': a_form,
        'profile': profile,
        'payments': payments,
        'custom_builds': custom_builds,
    }

    return render(request, 'user_profile.html', context)

@login_required
def custom_build_view(request):
    form = CustomBuildForm()

    if request.method == 'POST':
        form = CustomBuildForm(request.POST)
        if form.is_valid():
            build = form.save(commit=False)
            build.user = request.user
            build.save()
            return redirect('custom_build')  # reload page

    # Only show current user’s latest request
    latest_build = CustomBuildRequest.objects.filter(user=request.user).order_by('-created_at').first()

    return render(request, 'custom_build.html', {
        'form': form,
        'latest_build': latest_build,
    })

#invoice
@login_required


def generate_invoice(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    # ✅ Check both conditions
    if not payment.is_successful or payment.order_status != "delivered":
        return HttpResponse("Invoice unavailable. Order not delivered yet.", status=403)

    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="invoice_{payment.id}.pdf"'

    # Create the PDF object using reportlab
    p = canvas.Canvas(response, pagesize=letter)

    # Invoice content
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 750, "Laptop Store - Payment Invoice")

    p.setFont("Helvetica", 12)
    p.drawString(50, 720, f"Invoice ID: {payment.id}")
    p.drawString(50, 700, f"User: {payment.user.username} (ID: {payment.user.id})")
    p.drawString(50, 680, f"Laptop: {payment.laptop.model} (ID: {payment.laptop.id})")
    p.drawString(50, 660, f"Price: ₹{payment.amount}")
    p.drawString(50, 640, f"Delivery Method: {payment.delivery_method.capitalize()}")
    p.drawString(50, 620, f"Paid At: {payment.paid_at.strftime('%Y-%m-%d %H:%M:%S')}")
    p.drawString(50, 600, f"Order Status: {payment.order_status.capitalize()}")

    p.showPage()
    p.save()

    return response

def admin_dashboard(request):
    payments = Payment.objects.filter(is_successful=True, is_confirmed_by_admin=True)

    total_orders = payments.count()
    total_revenue = payments.aggregate(total=Sum('amount'))['total'] or 0

    last_7_days = now().date() - timedelta(days=6)
    raw_data = (
        payments.filter(paid_at__date__gte=last_7_days)
        .extra({'day': "DATE(paid_at)"})
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    today = now().date()
    labels = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    data_dict = {
        (entry['day'] if isinstance(entry['day'], str) else entry['day'].strftime('%Y-%m-%d')): entry['count']
        for entry in raw_data
    }
    data = [data_dict.get(label, 0) for label in labels]

    success_count = Payment.objects.filter(is_successful=True).count()
    failed_count = Payment.objects.filter(is_successful=False).count()

    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'labels': labels,
        'data': data,
        'success_count': success_count,
        'failed_count': failed_count,
    }
    return render(request, 'admin_dashboard.html', context)
#Review
@login_required
def submit_review(request, laptop_id):
    laptop = get_object_or_404(Laptop, id=laptop_id)
    reviews = Review.objects.filter(laptop=laptop).order_by('-created_at')

    # 🔁 Paginate reviews
    paginator = Paginator(reviews, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.laptop = laptop
            review.save()
            messages.success(request, "Your review has been submitted!")
            return redirect('submit_review', laptop_id=laptop.id)
    else:
        form = ReviewForm()

    return render(request, 'review_form.html', {
        'laptop': laptop,
        'form': form,
        'page_obj': page_obj,
    })

#Compare
def compare_laptops(request):
    laptop_ids = request.GET.getlist('ids')  # e.g., /compare/?ids=1&ids=2
    if not laptop_ids:
        return render(request, 'compare_laptops.html', 
        {
            'laptops': [],
            'min_price': None,
            'max_ram': None,
            'message': "No laptops selected for comparison."
        })
    laptops = get_list_or_404(Laptop, id__in=laptop_ids)
    min_price = min(laptops, key=lambda l: l.price).price
    max_ram = max(laptops, key=lambda l: int(l.ram.replace("GB", "").strip())).ram if laptops[0].ram else None

    return render(request, 'compare_laptops.html', {
        'laptops': laptops,
        'min_price': min_price,
        'max_ram': max_ram
    })

from django.shortcuts import render
from .models import Laptop

def laptop_list(request):
    ram_filter = request.GET.get('ram')  # e.g., ?ram=16
    laptops = Laptop.objects.all()

    if ram_filter:
        try:
            ram_value = int(ram_filter)
            # assuming Laptop.ram is stored as string like "16GB"
            laptops = laptops.filter(ram__icontains=f"{ram_value}GB")
        except ValueError:
            pass  # ignore if not a number

    return render(request, 'laptop_list.html', {'laptops': laptops})

    return render(request, 'compare.html', {'laptops': laptops})
#customer support
@login_required
def customer_support(request):
    if request.method == 'POST':
        form = CustomerSupportForm(request.POST)
        if form.is_valid():
            support = form.save(commit=False)
            support.user = request.user
            support.save()
            return redirect('support_success')
    else:
        form = CustomerSupportForm()
    previous_tickets = CustomerSupport.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'customer_support_form.html', {
        'form': form,
        'name': request.user.get_full_name(),
        'email': request.user.email,
        'previous_tickets': previous_tickets,
    })
def support_success(request):
    return render(request, 'support_success.html')
@login_required
def my_support_tickets(request):
    tickets = CustomerSupport.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'support/my_tickets.html', {'tickets': tickets})
#return
@login_required
def return_laptop(request):
    if request.method == 'POST':
        form = ReturnRequestForm(request.user, request.POST)
        if form.is_valid():
            return_request = form.save(commit=False)
            return_request.user = request.user
            return_request.save()
            return redirect('return_success')
    else:
        form = ReturnRequestForm(request.user)

    return render(request, 'return_form.html', {'form': form})

@login_required
def return_success(request):
    return render(request, 'return_success.html')

#laptoptypr
def filter_by_category(request, category_type):
    if category_type == 'business':
        laptops = Laptop.objects.filter(ram__lt=16)
        category_name = "Business Laptops"
    elif category_type == 'super':
        laptops = Laptop.objects.filter(ram__gte=16)
        category_name = "Super Laptops"
    else:
        laptops = Laptop.objects.none()
        category_name = "Unknown Category"

    return render(request, 'category_laptops.html', {
        'laptops': laptops,
        'category_name': category_name
    })
@staff_member_required
def sales_forecast(request):
    image_path = generate_sales_prediction()
    if not image_path:
        return render(request, 'admin/sales_forecast.html', {
            'error_message': "Not enough purchase data available for prediction."
        })
    return render(request, 'admin/sales_forecast.html', {'image_path': image_path})

#eta
from django.http import JsonResponse

def get_eta(request):
    pincode = request.GET.get('pincode')
    eta = "5-7 days"  # Default fallback

    # You can create a more dynamic rule-based mapping here
    if pincode.startswith("11"):  # Delhi
        eta = "2-3 days"
    elif pincode.startswith("40"):  # Mumbai
        eta = "3-4 days"
    elif pincode.startswith("56"):  # Bangalore
        eta = "4-5 days"

    return JsonResponse({'eta': eta})

#search

from django.http import JsonResponse
from .models import Laptop

def search_suggestions(request):
    query = request.GET.get('q', '')
    suggestions = []

    if query:
        laptops = Laptop.objects.filter(name__icontains=query)[:5]  # Top 5 matches
        for laptop in laptops:
            suggestions.append({'id': laptop.id, 'name': laptop.name})

    return JsonResponse({'suggestions': suggestions})

@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user
        user.delete()  # deletes user from DB
        messages.success(request, "Your account has been deleted successfully.")
        return redirect("login")  # or login page
    return render(request, "delete_account.html")

