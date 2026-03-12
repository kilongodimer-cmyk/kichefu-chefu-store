from django.shortcuts import redirect
from django.urls import reverse


class BrandIdentityWatermarkMiddleware:
    """Injects the Kichefu-Chefu brand watermark across every page."""

    STYLE_BLOCK = (
        "<style id=\"brand-identity-watermark\">"
        ":root{--brand-watermark:url('data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A//www.w3.org/2000/svg%27%20width%3D%27200%27%20height%3D%27220%27%20viewBox%3D%270%200%20200%20220%27%3E%3Crect%20width%3D%27200%27%20height%3D%27220%27%20fill%3D%27none%27/%3E%3Cpath%20d%3D%27M25%20150L50%2075L90%20150L110%2075L150%20150L175%2075V185H25Z%27%20fill%3D%27%23070707%27/%3E%3Ccircle%20cx%3D%2750%27%20cy%3D%2075%27%20r%3D%276%27%20fill%3D%27%23070707%27/%3E%3Ccircle%20cx%3D%20100%27%20cy%3D%2064%27%20r%3D%276%27%20fill%3D%27%23070707%27/%3E%3Ccircle%20cx%3D%20150%27%20cy%3D%2075%27%20r%3D%276%27%20fill%3D%27%23070707%27/%3E%3Ctext%20x%3D%27100%27%20y%3D%20203%27%20text-anchor%3D%27middle%27%20font-family%3D%27Bebas%20Neue%27%20font-size%3D%2725%27%20font-weight%3D%27700%27%20fill%3D%27%23070707%27%3EKICHEFU-CHEFU%3C/text%3E%3Ctext%20x%3D%27100%27%20y%3D%20217%27%20text-anchor%3D%27middle%27%20font-family%3D%27Poppins%27%20font-size%3D%2712%27%20font-weight%3D%27300%27%20letter-spacing%3D%277%27%20fill%3D%27%23070707%27%3ESTORE%3C/text%3E%3C/svg%3E');}"
        "body{position:relative;isolation:isolate;}"
        "body::before{content:'';position:fixed;inset:0;z-index:-1;pointer-events:none;opacity:0.12;"
        "background-image:var(--brand-watermark);background-repeat:repeat;background-size:200px%20auto;"
        "background-position:0%200;background-attachment:fixed;}"
        "</style>"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        content_type = response.get("Content-Type", "")
        if (
            response.status_code == 200
            and not getattr(response, "streaming", False)
            and "text/html" in content_type.lower()
        ):
            marker = b"brand-identity-watermark"
            if marker not in response.content:
                try:
                    content = response.content.decode(response.charset)
                except Exception:
                    return response

                head_close = content.lower().find("</head>")
                if head_close != -1:
                    patched = f"{content[:head_close]}{self.STYLE_BLOCK}{content[head_close:]}"
                    response.content = patched.encode(response.charset)
                    if response.has_header("Content-Length"):
                        response["Content-Length"] = len(response.content)

        return response


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
