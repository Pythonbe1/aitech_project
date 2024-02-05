from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.views.generic import TemplateView


class LoginView(TemplateView):
    template_name = 'account/login.html'

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to the success URL upon successful login
            return redirect('safety_detection:success')
        # Assuming 'success' is the name of the URL pattern for SuccessView
        else:
            # Display an error message if authentication fails.
            error_message = 'Invalid username or password.'
            return render(request, self.template_name, {'error_message': error_message})
