from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny


def user_data(user, token):
    return {
        "token": token.key,
        "user": {
            "id":         user.id,
            "email":      user.email,
            "full_name":  user.get_full_name() or user.username,
            "job_title":  getattr(user, 'profile', None) and user.profile.job_title or "",
            "department": getattr(user, 'profile', None) and user.profile.department or "",
        }
    }


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email    = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password') or ''

        if not email or not password:
            return Response({'message': 'Email and password are required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Django auth uses username; we treat email as username
        user = authenticate(request, username=email, password=password)
        if not user:
            # Also try matching by email field (if username != email)
            try:
                u = User.objects.get(email=email)
                user = authenticate(request, username=u.username, password=password)
            except User.DoesNotExist:
                pass

        if not user:
            return Response({'message': 'Invalid email or password.'},
                            status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({'message': 'Account is disabled.'},
                            status=status.HTTP_403_FORBIDDEN)

        token, _ = Token.objects.get_or_create(user=user)
        return Response(user_data(user, token), status=status.HTTP_200_OK)


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email      = (request.data.get('email') or '').strip().lower()
        password   = request.data.get('password') or ''
        full_name  = (request.data.get('fullName') or '').strip()
        job_title  = (request.data.get('jobTitle') or '').strip()
        department = (request.data.get('department') or '').strip()

        # Validate required fields
        if not email:
            return Response({'email': ['Email is required.']},
                            status=status.HTTP_400_BAD_REQUEST)
        if not password:
            return Response({'password': ['Password is required.']},
                            status=status.HTTP_400_BAD_REQUEST)
        if not full_name:
            return Response({'fullName': ['Full name is required.']},
                            status=status.HTTP_400_BAD_REQUEST)

        # Check email uniqueness
        if User.objects.filter(email=email).exists():
            return Response({'email': ['An account with this email already exists.']},
                            status=status.HTTP_400_BAD_REQUEST)

        # Validate password strength
        try:
            validate_password(password)
        except ValidationError as e:
            return Response({'password': list(e.messages)},
                            status=status.HTTP_400_BAD_REQUEST)

        # Split full name into first/last
        parts = full_name.split(' ', 1)
        first = parts[0]
        last  = parts[1] if len(parts) > 1 else ''

        user = User.objects.create_user(
            username   = email,   # use email as username
            email      = email,
            password   = password,
            first_name = first,
            last_name  = last,
        )

        # Save extra profile fields
        try:
            from .models import UserProfile
            UserProfile.objects.create(user=user, job_title=job_title, department=department)
        except Exception:
            pass  # profile is optional

        token, _ = Token.objects.get_or_create(user=user)
        return Response(user_data(user, token), status=status.HTTP_201_CREATED)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        if not email:
            return Response({'message': 'Email is required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        # Always return 200 to prevent email enumeration
        # In production: send real reset email via Django's PasswordResetForm
        return Response({'message': 'If that email exists, a reset link has been sent.'},
                        status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
        return Response({'message': 'Logged out.'}, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user  = request.user
        token = Token.objects.get(user=user)
        return Response(user_data(user, token))
