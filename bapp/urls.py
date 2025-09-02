from django.urls import path,include
from .import views
from django.contrib.auth import views as auth_views
from bapp.views import generate_invoice,admin_dashboard
from .views import submit_review,sales_forecast



urlpatterns=[
    # main page
    path('', views.home_view, name='home'),
    path('laptop/<int:id>/', views.laptop_detail, name='laptop_detail'),
    #login
    path('dashboard', views.dashboard_view, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    #admin add laptop
    path('add-laptop/', views.add_laptop_view, name='add_laptop'),
    path('edit-laptop/<int:id>/', views.edit_laptop_view, name='edit_laptop'),
    #cart
    path('add-to-cart/<int:laptop_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('checkout/', views.checkout, name='checkout'),
     path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    #payment
    path('buy-now/<int:laptop_id>/', views.buy_now, name='buy_now'),
    path('payment/<int:laptop_id>/', views.payment_gateway, name='payment_gateway'),
    path('payment-success/<int:payment_id>/', views.payment_success, name='payment_success'),
    #Address
    path('address/', views.add_or_update_address, name='add_or_update_address'),
    #Profile
    path('profile/', views.user_profile, name='user_profile'),
    #custombuild
    path('custom-build/', views.custom_build_view, name='custom_build'),
    #searchs
    path('change-password/', auth_views.PasswordChangeView.as_view(
        template_name='change_password.html',
        success_url='/password-changed-successfully/'
    ), name='change_password'),
    path('password-changed-successfully/', auth_views.PasswordChangeDoneView.as_view(
        template_name='change_password_done.html'
    ), name='password_change_done'),   
    #invoice
    path('invoice/<int:payment_id>/',generate_invoice, name='generate_invoice'),
    #analysis
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    #review
    path('review/<int:laptop_id>/', submit_review, name='submit_review'),
    #compare
    path('compare/', views.compare_laptops, name='compare_laptops'),
    path('compare-list/', views.laptop_list, name='laptop_list'),
    #customer support
    path('support/', views.customer_support, name='customer_support'),
    path('success/', views.support_success, name='support_success'),
    path('my-support/', views.my_support_tickets, name='my_support_tickets'),
    path('return/', views.return_laptop, name='return_laptop'),
    path('return/success/', views.return_success, name='return_success'),
    #forgot password
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    #type laptop
    path('category/<str:category_type>/', views.filter_by_category, name='category_filter'),
    #AI
    path('admin/sales-forecast/',sales_forecast, name='sales_forecast'),
    #Ets
    path('get-eta/', views.get_eta, name='get_eta'),
    #chatbot
    path("chatbot/", include("chatbot.urls")),
    #delete
    path("delete/", views.delete_account, name="delete_account"),
]


