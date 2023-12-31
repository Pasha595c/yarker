from django.shortcuts import render, redirect
from django.views import View
from django.core.exceptions import ValidationError

# from users.forms import RegistrationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth import get_user_model, login, authenticate, logout
from django.contrib.auth.views import LoginView
from django.contrib.sites.shortcuts import get_current_site
from users.utils import send_email_for_verify
from .forms import UserCreationForm, AuthenticationForm

User = get_user_model()
"""
Обработка регистрации нового пользователя.
Отправка письма с ссылкой активации, только если пользователь не подтвердил почту
Возвращается страница регистрации с формой или перенаправление на страницу успешной регистрации.
"""


def RegisterView(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()

            if not user.email_verify:
                send_email_for_verify(request, user)
            return redirect("registration_success")
    else:
        form = UserCreationForm()
    return render(request, "users/registration/registration.html", {"form": form})


class MyLoginView(LoginView):
    """Представление авторизации пользователей"""

    form_class = AuthenticationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_site = get_current_site(self.request)
        context.update(
            {
                self.redirect_field_name: self.get_redirect_url(),
                "site": current_site,
                "site_name": current_site.name,
                **(self.extra_context or {}),
                "title": f"Авторизация на сайте {current_site.domain}",
            }
        )
        return context


class EmailVerifyView(View):
    """Представление подтверждения Email пользователя"""

    def get(self, request, uidb64, token):
        user = self.get_user(uidb64)
        if user is not None and default_token_generator.check_token(user, token):
            user.email_verify = True
            user.save()
            login(request, user)  # Войти в систему после успешной активации
            request.session["activation_success"] = True
            return redirect("activation-success")
        return redirect("invalid_verify")

    @staticmethod
    def get_user(uidb64):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            User.DoesNotExist,
            ValidationError,
        ):
            user = None
        return user


def user_logoutView(request):
    logout(request)
    return redirect("main")
