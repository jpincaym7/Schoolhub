from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from apps.users.models import Module, ModulePermission

class DashboardView(LoginRequiredMixin, TemplateView):
    login_url = '/users/login/'
    template_name = 'modules/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user_type = self.request.user.user_type

        # Filtrar los módulos a los que el usuario tiene acceso
        user_permissions = ModulePermission.objects.filter(user_type=user_type, can_view=True)
        accessible_modules = Module.objects.filter(id__in=user_permissions.values('module')).order_by('order')
        
        context['user_modules'] = accessible_modules
        
        return context

class ModuleManagementView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'modules/modules.html'
    
    def test_func(self):
        return self.request.user.user_type == 'admin'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modules'] = Module.objects.all().order_by('order')
        return context
    