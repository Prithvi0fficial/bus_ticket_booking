from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameAuthBackend(ModelBackend):
    """Authenticate using either email or username"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Search for the user by username OR email
            user = User.objects.filter(Q(username=username) | Q(email=username)).first()
            if user and user.check_password(password):  # Verify password
                return user
        except User.DoesNotExist:
            return None

