from .models import Profile

def user_profile_context(request):
    if request.user.is_authenticated:
        try:
            return {'user_profile': request.user.profile}
        except Profile.DoesNotExist:
            return {'user_profile': None}
    return {'user_profile': None}
