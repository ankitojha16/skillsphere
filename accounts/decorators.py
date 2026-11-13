from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.views import redirect_to_login

def recruiter_required(view_func):
    """
    Authorization decorator that restricts access strictly to recruiters, staff, and superusers.
    
    Response behavior:
    - Anonymous users: redirect to login (or return HTTP 401 for AJAX/API requests).
    - Authenticated non-recruiters (students): redirect to /dashboard/ with an informational warning
      (or return HTTP 403 Forbidden for AJAX/API requests).
    - Authorized users: request.user.is_staff, request.user.is_superuser, or profile.role == 'recruiter'.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        is_ajax_or_api = (
            request.headers.get('x-requested-with') == 'XMLHttpRequest' or
            request.headers.get('accept', '').startswith('application/json') or
            request.path.endswith('/shortlist/') or
            request.path.endswith('/invite/') or
            request.path.startswith('/api/')
        )

        if not request.user.is_authenticated:
            if is_ajax_or_api:
                return JsonResponse({'status': 'error', 'message': 'Authentication required.'}, status=401)
            return redirect_to_login(request.get_full_path())

        is_authorized = (
            request.user.is_staff or
            request.user.is_superuser or
            (hasattr(request.user, 'profile') and request.user.profile is not None and getattr(request.user.profile, 'role', '') == 'recruiter')
        )

        if not is_authorized:
            if is_ajax_or_api:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Forbidden: Recruiter or administrator access required.'
                }, status=403)
            messages.warning(
                request,
                "Access Restricted: The Recruiter Talent Portal is reserved for verified talent partners and recruiters."
            )
            return redirect('dashboard:index')

        return view_func(request, *args, **kwargs)

    return _wrapped_view
