from django.contrib import admin
from django.urls import path
from accounts import views as account_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', account_views.login_view, name='login'),
    path('logout/', account_views.logout_view, name='logout'),
    path('customer/dashboard/', account_views.customer_dashboard, name='customer_dashboard'),
    path('driver/dashboard/', account_views.driver_dashboard, name='driver_dashboard'),
]

