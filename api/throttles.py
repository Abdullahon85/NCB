# api/throttles.py
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """
    Rate limiting for login attempts to prevent brute force attacks.
    Maximum 5 login attempts per hour.
    """
    scope = 'login'
    rate = '5/hour'
