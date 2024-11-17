from django.urls import path, include
from .views import BaseInfoView
from offers_app.views import OfferDetailView
from orders_app.views import OrderCountView, CompletedOrderCountView
from profile_app.views import ProfileView
from auth_app.views import LoginView, RegisterView

# SETTINGS.PY die APPS ergänzen

urlpatterns = [ 
    path('offers/', include('offers_app.urls')),   
    path('offerdetails/<int:pk>/', OfferDetailView.as_view()),
    path('orders/', include('orders_app.urls')),
    path('order-count/<int:pk>/', OrderCountView.as_view()),
    path('completed-order-count/<int:pk>/', CompletedOrderCountView.as_view()),
    path('base-info/', BaseInfoView.as_view()),
    path('profile/<int:pk>/', ProfileView.as_view()),
    path('profiles/', include('profile_app.urls')),
    path('reviews/', include('review_app.urls')),
    path('login/', LoginView.as_view()),
    path('registration/', RegisterView.as_view()),
]