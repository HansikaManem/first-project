from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from accounts.forms import CustomUserCreationForm, CustomLoginForm
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from .models import DeliveryRequest, Delivery, Feedback
from .forms import DeliveryRequestForm 
from .models import CustomUser 
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from .forms import DeliveryForm
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.backends import ModelBackend 
from .models import Delivery, next_status, ALLOWED_STATUS_TRANSITIONS
from .forms import DeliveryStatusForm
from accounts.templatetags.delivery_tags import get_next_status 
from .forms import FeedbackForm
from django.db.models import Avg
from .forms import UserProfileEditForm


def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            login(
                request,
                user,
                backend='django.contrib.auth.backends.ModelBackend'
            )

            return redirect('customer_dashboard' if user.role == 'customer'
                            else 'driver_dashboard')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})



def login_view(request):
    if request.method == "POST":
        email    = request.POST.get("email")
        password = request.POST.get("password")
        role_in_form = request.POST.get("role")

        user = authenticate(request, email=email, password=password)

        if user is None:
            return HttpResponse("Invalid credentials", status=401)

        if user.role != role_in_form:
            return HttpResponse("Role mismatch", status=401)

        login(request, user)

        if role_in_form == "customer":
            return redirect("customer_dashboard")
        else:
            return redirect("driver_dashboard")

    return render(request, "accounts/login.html", {
        "role_choices": [("customer", "Customer"), ("driver", "Driver")]
    })



@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def customer_dashboard(request):
    if request.user.role != "customer":
        return redirect("driver_dashboard")
    return render(request, "accounts/customer_dashboard.html")


@login_required
def driver_dashboard(request):
    pending_deliveries = Delivery.objects.filter(status='pending', driver__isnull=True)
    return render(request, 'accounts/driver_dashboard.html', {'deliveries': pending_deliveries})


@login_required
def create_delivery(request):
    if request.method == 'POST':
        form = DeliveryForm(request.POST)
        if form.is_valid():
            delivery = form.save(commit=False)
            delivery.customer = request.user
            delivery.status = 'pending'
            delivery.save()
            return redirect('customer_deliveries')
        else:
            print("Form errors:", form.errors)
    else:
        form = DeliveryForm()
    return render(request, 'accounts/create_delivery.html', {'form': form})


@login_required
def pending_deliveries(request):
    if request.user.role == 'driver':
        deliveries = Delivery.objects.filter(status='pending', driver__isnull=True)
        return render(request, 'accounts/pending_deliveries.html', {'deliveries': deliveries})
    else:
        return redirect('driver_dashboard')


@require_POST
@login_required
def accept_delivery(request, delivery_id):
    if request.user.role != 'driver':
        return redirect('driver_dashboard')

    try:
        with transaction.atomic():
            delivery = Delivery.objects.select_for_update().get(id=delivery_id)

            if delivery.status == 'pending' and delivery.driver is None:
                delivery.driver = request.user
                delivery.status = 'accepted'
                delivery.save()
                messages.success(request, 'You have successfully accepted the delivery.')
            else:
                messages.error(request, 'This delivery has already been accepted by another driver.')

    except Delivery.DoesNotExist:
        messages.error(request, 'Delivery not found.')

    return redirect('pending_list')


@login_required
def my_deliveries(request):
    if request.user.role == 'driver':
        deliveries = Delivery.objects.filter(driver=request.user).exclude(status='delivered')
        return render(request, 'accounts/my_deliveries.html', {'deliveries': deliveries})
    else:
        return render(request, 'accounts/my_deliveries.html', {'deliveries': []})


@login_required
def mark_as_completed(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id, driver=request.user)

    if request.method == 'POST':
        delivery.status = 'completed'
        delivery.save()
        return redirect('accepted_deliveries')

    return redirect('accepted_deliveries')


@login_required
def customer_deliveries(request):
    if request.user.role != 'customer':
        return redirect('login')

    deliveries = Delivery.objects.filter(customer=request.user).order_by('-created_at')
    return render(request, 'accounts/customer_deliveries.html', {'deliveries': deliveries})


@login_required
def edit_delivery(request, pk):
    delivery = get_object_or_404(Delivery, pk=pk, customer=request.user)

    if delivery.status != 'pending':
        return render(request, 'accounts/access_denied.html', {'message': 'Only pending deliveries can be edited.'})

    if request.method == 'POST':
        form = DeliveryForm(request.POST, instance=delivery)
        if form.is_valid():
            form.save()
            return redirect('customer_deliveries')
    else:
        form = DeliveryForm(instance=delivery)

    return render(request, 'accounts/edit_delivery.html', {'form': form})


@login_required
def cancel_delivery(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id, customer=request.user, status='pending')
    delivery.delete()
    return redirect('customer_deliveries')


@login_required
def driver_accepted_deliveries(request):
    if request.user.role != 'driver':
        return redirect('login')
    deliveries = Delivery.objects.filter(driver=request.user).order_by('-created_at')
    return render(request, 'accounts/driver_accepted_deliveries.html', {'deliveries': deliveries})


def next_status(current_status):
    transition_map = {
        "assigned": "in_transit",
        "in_transit": "delivered",
    }
    return transition_map.get(current_status)


@login_required
def driver_update_status(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id, driver=request.user)

    nxt = next_status(delivery.status)
    if not nxt:
        return redirect("accepted_deliveries")

    if request.method == "POST":
        form = DeliveryStatusForm(request.POST, instance=delivery, current_status=delivery.status)
        if form.is_valid():
            form.save()
            return redirect("accepted_deliveries")
    else:
        form = DeliveryStatusForm(instance=delivery, current_status=delivery.status)

    return render(request, "accounts/driver_update_status.html", {
        "delivery": delivery, "form": form
    })


@login_required
def update_delivery_status(request, delivery_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    delivery = get_object_or_404(Delivery, id=delivery_id)
    if request.user != delivery.driver:
        return HttpResponseForbidden("Not your delivery")

    next_stat = get_next_status(delivery.status)
    if not next_stat:
        return HttpResponseBadRequest("No further transition allowed")

    with transaction.atomic():
        locked = Delivery.objects.select_for_update().get(pk=delivery.pk)

        client_status = request.POST.get("current_status")
        if client_status and client_status != locked.status:
            return HttpResponseBadRequest("Delivery state changed, please refresh")

        if locked.status != delivery.status:
            return HttpResponseBadRequest("Delivery state changed, please refresh")

        locked.status = next_stat
        locked.save()

    messages.success(request, f"Delivery marked as “{next_stat}”.")
    return redirect("my_deliveries")


@login_required
def customer_track(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id, customer=request.user)
    return render(request, "accounts/customer_track.html", {"delivery": delivery})


@login_required
def give_feedback(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id)

    if delivery.customer != request.user:
        return HttpResponseForbidden("You can't rate this delivery.")

    if delivery.status != 'Delivered':
        return HttpResponseBadRequest("Feedback allowed only after delivery.")

    if Feedback.objects.filter(delivery=delivery).exists():
        return HttpResponseBadRequest("Feedback already submitted.")

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.delivery = delivery
            feedback.customer = request.user
            feedback.save()
            return redirect('customer_profile')
    else:
        form = FeedbackForm()

    return render(request, 'accounts/give_feedback.html', {
        'form': form,
        'delivery': delivery
    })


@login_required
def profile(request):
    if request.user.role == 'customer':
        deliveries = Delivery.objects.filter(customer=request.user)
    elif request.user.role == 'driver':
        deliveries = Delivery.objects.filter(driver=request.user, status='Delivered')
    else:
        deliveries = []

    return render(request, 'accounts/profile.html', {'deliveries': deliveries})


@login_required
def edit_feedback(request, delivery_id):
    feedback = get_object_or_404(Feedback, delivery_id=delivery_id, customer=request.user)

    if request.method == 'POST':
        feedback.rating = request.POST.get('rating')
        feedback.comment = request.POST.get('comment')
        feedback.save()
        messages.success(request, "Feedback updated.")
        return redirect('customer_profile')

    return render(request, 'accounts/edit_feedback.html', {'feedback': feedback})


@login_required
def delete_feedback(request, delivery_id):
    feedback = get_object_or_404(Feedback, delivery_id=delivery_id, customer=request.user)
    if request.method == 'POST':
        feedback.delete()
        messages.success(request, "Feedback deleted.")
        return redirect('customer_profile')
    return render(request, 'accounts/delete_feedback_confirm.html', {'feedback': feedback})


@login_required
def customer_profile(request):
    if request.user.role != 'customer':
        return redirect('dashboard')

    deliveries = Delivery.objects.filter(customer=request.user)
    return render(request, 'accounts/customer_profile.html', {
        'deliveries': deliveries,
        'user': request.user,
    })


@login_required
def driver_profile(request):
    if request.user.role != 'driver':
        return redirect('dashboard')

    completed_deliveries = Delivery.objects.filter(driver=request.user, status='Delivered')
    feedbacks = Feedback.objects.filter(delivery__in=completed_deliveries)
    avg_rating = feedbacks.aggregate(avg=Avg('rating'))['avg']

    return render(request, 'accounts/driver_profile.html', {
        'deliveries': completed_deliveries,
        'avg_rating': round(avg_rating or 0, 2),
        'feedbacks': feedbacks,
        'user': request.user,
    })


@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('customer_profile' if user.role == 'customer' else 'driver_profile')
    else:
        form = UserProfileEditForm(instance=user)

    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def edit_driver_profile(request):
    user_form    = UserProfileEditForm(instance=request.user)
    profile_form = ProfileUpdateForm(instance=request.user.profile)

    if request.method == "POST":
        user_form    = UserProfileEditForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated!")
            return redirect('driver_profile')

    return render(request, "accounts/edit_driver_profile.html", {
        "user_form": user_form,
        "profile_form": profile_form
    })
