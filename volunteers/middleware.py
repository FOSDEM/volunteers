from django.shortcuts import redirect
from django.urls import reverse

class EnforcePrivacyPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            v = getattr(request.user, 'volunteer', None)
            if v and not v.privacy_policy_accepted_at:
                allowed = {
                    reverse('privacy_policy'),
                    reverse('privacy_policy_consent'), 
                    reverse('logout'),
                }
                if request.path not in allowed and not request.path.startswith('/static/'):
                    return redirect('privacy_policy_consent')
        return self.get_response(request)
