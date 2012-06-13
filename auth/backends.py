from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

class ModelBackendFlexible(ModelBackend):
    
    """
    Allow user login by username or email.
    
    Use this by adding the path to this class to 
    AUTHENTICATION_BACKENDS in settings, e.g.:
    
        AUTHENTICATION_BACKENDS = (
            ...
            'path.to.machete.auth.backends.ModelBackendFlexible',
            ...
        )
    
    """
    
    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(Q(username=username) | Q(email=username))
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None