def student_profile_context(request):
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        return {'student_profile': profile}
    return {'student_profile': None}
