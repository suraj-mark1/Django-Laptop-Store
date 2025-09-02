from django import forms
from django.contrib.auth.models import User
from .models import Laptop,Payment
from .models import ReturnRequest,CustomerSupport, UserProfile, Address,CustomBuildRequest,Review

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
class LaptopForm(forms.ModelForm):
    class Meta:
        model = Laptop
        fields = ['brand', 'model', 'ram', 'processor', 'display', 'storage','gpu','price', 'image']
class quantityUpdateForm(forms.Form):
    quantity=forms.IntegerField(min_value=1)
class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['full_name', 'phone', 'address_line', 'city', 'state', 'zip_code', 'country']
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone']
class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['address_line', 'city', 'state', 'zip_code', 'country']
class CustomBuildForm(forms.ModelForm):
    class Meta:
        model = CustomBuildRequest
        fields = ['ram', 'cpu', 'gpu', 'display', 'monitor', 'keyboard', 'ssd', 'storage']
class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['address', 'delivery_method', 'cash_option', 'card_name', 'pin']

    def clean(self):
        cleaned_data = super().clean()
        delivery_method = cleaned_data.get('delivery_method')
        card_name = cleaned_data.get('card_name')
        pin = cleaned_data.get('pin')
        cash_option = cleaned_data.get('cash_option')

        if delivery_method == 'online':
            if not card_name or not pin:
                raise forms.ValidationError("Card Name and PIN are required for online payments.")
        elif delivery_method == 'cash':
            if not cash_option:
                raise forms.ValidationError("Select one of the cash options.")

        return cleaned_data       
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
class CustomerSupportForm(forms.ModelForm):
    class Meta:
        model = CustomerSupport
        fields = ['phone', 'complaint']
        widgets = {
            'complaint': forms.Textarea(attrs={'rows': 5}),
        }
class ReturnRequestForm(forms.ModelForm):
    class Meta:
        model = ReturnRequest
        fields = ['order', 'reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order'].queryset = user.order_set.all()