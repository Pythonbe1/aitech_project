from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class SuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'safety_detection/main.html'
