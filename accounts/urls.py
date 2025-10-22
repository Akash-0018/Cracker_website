from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile_update'),
]