from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import CustomUser

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    template_name = 'accounts/profile_update.html'
    fields = ['phone_number', 'address', 'profile_picture', 'date_of_birth']
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Your profile has been updated successfully!')
        return super().form_valid(form)
