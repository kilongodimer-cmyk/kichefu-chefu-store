from django.shortcuts import redirect
from django.urls import reverse

class AdminSuperuserRequiredMiddleware:
    """
    Middleware: bloque l'accès à /admin/ pour tout utilisateur non superuser.
    Redirige vers l'accueil si non connecté ou non superuser.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            if not getattr(request, "user", None) or not request.user.is_authenticated:
                return redirect(reverse('home'))

            is_admin_role = bool(
                request.user.is_superuser
                or request.user.groups.filter(name="Admin").exists()
            )
            if not is_admin_role:
                return redirect(reverse('home'))
        return self.get_response(request)
