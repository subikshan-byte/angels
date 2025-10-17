from django.shortcuts import redirect

class DomainRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        if "190.92.175.39" in host:
            new_url = request.build_absolute_uri().replace("190.92.175.39:8000", "angels-glamnglow.in")
            return redirect(new_url)
        return self.get_response(request)
