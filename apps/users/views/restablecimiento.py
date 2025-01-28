from django.contrib.auth.views import (
    PasswordResetView as DjangoPasswordResetView,
    PasswordResetConfirmView as DjangoPasswordResetConfirmView,
    PasswordResetDoneView as DjangoPasswordResetDoneView,
    PasswordResetCompleteView as DjangoPasswordResetCompleteView
)
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

class PasswordResetView(DjangoPasswordResetView):
    template_name = 'users/password_reset_form.html'
    email_template_name = 'users/password_reset_email.html'
    success_url = reverse_lazy('users:password_reset_done')

    def send_mail(self, subject_template_name, email_template_name, context, from_email, to_email, html_email_template_name=None):
        """
        Override send_mail to include both HTML and plain-text versions in the email.
        """
        # Render text and HTML templates
        subject = render_to_string(subject_template_name, context).strip()
        text_content = render_to_string(email_template_name, context)
        html_content = render_to_string(html_email_template_name or email_template_name, context)

        # Create email message
        email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        email.attach_alternative(html_content, "text/html")
        email.send()

class PasswordResetConfirmView(DjangoPasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')

class PasswordResetDoneView(DjangoPasswordResetDoneView):
    template_name = 'users/password_reset_done.html'

class PasswordResetCompleteView(DjangoPasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'
