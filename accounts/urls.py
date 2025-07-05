from django.urls import include, path
from . import views
from accounts.views import edit_delivery

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/customer/', views.customer_dashboard, name='customer_dashboard'),
    path('dashboard/driver/', views.driver_dashboard, name='driver_dashboard'),
    path('my_deliveries/', views.my_deliveries, name='my_deliveries'),
    path("deliveries/pending/", views.pending_deliveries, name="pending_list"),
    path("delivery/create/", views.create_delivery, name="delivery_new"),
    path('delivery/accept/<int:delivery_id>/', views.accept_delivery, name='accept_delivery'),
    path('deliveries/accepted/', views.driver_accepted_deliveries, name='accepted_deliveries'),
    path('deliveries/complete/<int:delivery_id>/', views.mark_as_completed, name='mark_completed'),
    path('deliveries/my/', views.customer_deliveries, name='customer_deliveries'),
    path('delivery/cancel/<int:delivery_id>/', views.cancel_delivery, name='cancel_delivery'),
    path('delivery/edit/<int:delivery_id>/', views.edit_delivery, name='edit_delivery'),
    path('delivery/update_status/<int:delivery_id>/', views.update_delivery_status, name='update_delivery_status'),
    path('track/<int:delivery_id>/',views.customer_track,name='customer_track'),
    path('feedback/<int:delivery_id>/', views.give_feedback, name='give_feedback'),
    path('profile/driver/', views.driver_profile, name='driver_profile'),  
    path('profile/customer/', views.customer_profile, name='customer_profile'),
    path('profile/driver/edit/', views.edit_driver_profile, name='edit_driver_profile'),
    
    
]
