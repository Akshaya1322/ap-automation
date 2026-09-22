from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.audit_logs.services import log_action
from apps.authentication.models import Role, User
from apps.authentication.serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    UserSerializer,
)


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            username = request.data.get("username")
            user = User.objects.filter(username=username).first()
            log_action(
                action="LOGIN",
                entity_type="User",
                entity_id=user.id if user else "",
                description=f"{username} logged in",
                user=user,
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        return response


class LogoutView(APIView):
    def post(self, request):
        log_action(
            action="LOGOUT",
            entity_type="User",
            entity_id=request.user.id,
            description=f"{request.user.username} logged out",
        )
        return Response({"detail": "Logged out."}, status=status.HTTP_200_OK)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password updated successfully."})


class UserListView(generics.ListAPIView):
    """Used for populating approver/assignee dropdowns."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = User.objects.filter(is_active=True).order_by("first_name", "username")
        role = self.request.query_params.get("role")
        if role and role in Role.values:
            qs = qs.filter(role=role)
        return qs
