from django.views.generic import UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from apps.users.models import User
from apps.users.forms import UserProfileForm

class UserProfileDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'security/profile_detail.html'
    context_object_name = 'profile_user'

    def get_object(self, queryset=None):
        return self.request.user

class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'security/profile_edit.html'
    success_url = reverse_lazy('users:user_profile_detail')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Su perfil se actualizó correctamente.')
        return super().form_valid(form)
