from cProfile import Profile
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404, redirect, render
from .models import CustomUser, Delivery, DeliveryRequest
from .models import next_status
from .models import Feedback
from django.contrib.auth import get_user_model


class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        widget=forms.RadioSelect,
        label="Register as"
    )

    class Meta:
        model = CustomUser
        fields = ("username", "email", "role", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("That email is already registered.")
        return email


class CustomLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True})
    )

    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        widget=forms.Select(),
        label="Logging in as"
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("username")
        password = cleaned_data.get("password")
        role = cleaned_data.get("role")

        if email and password and role:
            user = authenticate(self.request, username=email, password=password)
            if user is None:
                raise forms.ValidationError("Invalid email or password.")

            if user.role != role:
                raise forms.ValidationError(
                    f"You selected “{role}”, but you're registered as “{user.role}”."
                )

            self.user_cache = user

        return cleaned_data

class DeliveryRequestForm(forms.ModelForm):
    class Meta:
        model  = DeliveryRequest
        fields = ("pickup_address", "dropoff_address", "package_note")
        widgets = {
            "package_note": forms.Textarea(attrs={"rows": 3}),
        }
class DeliveryForm(forms.ModelForm):
    class Meta:
        model = Delivery
        fields = ['pickup_address', 'dropoff_address', 'package_note'] 
        widgets = {
            'pickup_address': forms.TextInput(attrs={
                'placeholder': 'Enter pickup address'
            }),
            'dropoff_address': forms.TextInput(attrs={
                'placeholder': 'Enter dropoff address'
            }),
            'package_note': forms.Textarea(attrs={
                'placeholder': 'Enter any note about the package',
                'rows': 4
            }),
        }

def edit_delivery(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id, customer=request.user)

    if delivery.status != 'pending':
        return redirect('customer_deliveries') 

    if request.method == 'POST':
        form = EditDeliveryForm(request.POST, instance=delivery) # type: ignore
        if form.is_valid():
            form.save()  
            return redirect('customer_deliveries')
    else:
        form = EditDeliveryForm(instance=delivery) # type: ignore

    return render(request, 'accounts/edit_delivery.html', {'form': form})

class DeliveryStatusForm(forms.ModelForm):
    class Meta:
        model  = Delivery
        fields = ["status"]

    def __init__(self, *args, **kwargs):
        current_status = kwargs.pop("current_status")
        super().__init__(*args, **kwargs)

        nxt = next_status(current_status)

        self.fields["status"].choices = [
            (nxt, nxt.replace("_", " ").title())
        ] if nxt else []



class DeliveryStatusForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.current_status = kwargs.pop('current_status', None)
        super().__init__(*args, **kwargs)


        status_choices = {
            "assigned": [("in_transit", "In Transit")],
            "in_transit": [("completed", "Delivered")],
        }

        if self.current_status in status_choices:
            self.fields['status'].choices = status_choices[self.current_status]
        else:
            self.fields['status'].choices = []

    class Meta:
        model = Delivery
        fields = ['status']


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, i) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 3, 'maxlength': 200}),
        }
        labels = {
            'rating': 'Your Rating (1 to 5)',
            'comment': 'Comment (Optional)',
        }

User = get_user_model()

class UserProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser 
        fields = ['username', 'email'] 



class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']


#class EditProfileForm(forms.ModelForm):
#    class Meta:
#        model = Profile
#        fields = ['phone', 'profile_picture']