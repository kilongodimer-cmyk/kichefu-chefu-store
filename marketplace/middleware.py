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
        # Ne bloque pas les requêtes internes (static, media, login, logout)
        admin_path = request.path.startswith('/admin/')
        is_static = request.path.startswith('/static/') or request.path.startswith('/media/')
        is_login = request.path.startswith('/admin/login') or request.path.startswith('/admin/logout')
        if admin_path and not is_static and not is_login:
            if not request.user.is_authenticated or not request.user.is_superuser:
                try:
                    return redirect(reverse('home'))
                except Exception:
                    from django.http import HttpResponseRedirect
                    return HttpResponseRedirect('/')
        return self.get_response(request)
