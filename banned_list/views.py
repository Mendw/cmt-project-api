from banned_list.models import BannedEntity
from banned_list.serializers import BannedEntitySerializer, UserSerializer, SignupSerializer
from rest_framework import generics
from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_auth.views import (
    LoginView as LoginView_, LogoutView, PasswordChangeView as PasswordChangeView_
)
from rest_auth.registration.views import (
    RegisterView as RegisterView_
)
from rest_framework import status
from django.utils.translation import ugettext_lazy as _


class Index(APIView):
    """
    Returns a description of the API
    """

    def get(self, request, format=None):
        return Response([{
            'name': 'Banned List',
            'description': 'Returns a filtered list of banned entities, request must be authenticated',
            'url': request.build_absolute_uri('/banned/')
        }, {
            'name': 'User List',
            'description': 'Returns a list of users, request must be from super user',
            'url': request.build_absolute_uri('/users/')
        }, {
            'name': 'User Detail',
            'description': 'Returns details from an user, request must be from that user or a superuser',
            'url': request.build_absolute_uri('/users/<id>')    
        }, {
            'name': 'Login',
            'description': 'Returns an User\'s token when POST-ed its username and password. Password is case-insensitive',
            'url': request.build_absolute_uri('/auth')
        }, {
            'name': 'Logout',
            'description': 'Logs the current user out',
            'url': request.build_absolute_uri('/auth/logout')
        }, {
            'name': 'Sign Up',
            'description': 'Creates a new User when POST-ed a unique username and a password twice. Password is case-insensitive',
            'url': request.build_absolute_uri('/auth/signup')
        }, {
            'name': 'Password Change',
            'description': 'Changes the curren user\'s password when POST-ed the current password (as old_password) and the new password twice(as new_password1 and new password2)',
            'url': request.build_absolute_uri('/auth/password-change')
        }])


class BannedList(generics.ListAPIView):
    serializer_class = BannedEntitySerializer

    def get_queryset(self):
        filter_ = self.kwargs['filter'] if 'filter' in self.kwargs else None
        return BannedEntity.objects.filter(  # pylint: disable=no-member
            Q(is_sanctioned=True) &
            (
                Q(name__icontains=filter_) |
                Q(source__icontains=filter_) |
                Q(aliases__alias__icontains=filter_)
            )
        ) if filter_ != None else BannedEntity.objects.all()  # pylint: disable=no-member


class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class RegisterView(RegisterView_):
    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        if data:
            if 'password1' in data:
                data['password1'] = data['password1'].lower() 

            if 'password2' in data:
                data['password2'] = data['password2'].lower() 

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(self.get_response_data(user),
                        status=status.HTTP_201_CREATED,
                        headers=headers)


class LoginView(LoginView_):
    def post(self, request, *args, **kwargs):
        self.request = request
        data = self.request.data.copy()
        if data and 'password' in data:
            data['password'] = data['password'].lower()

        self.serializer = self.get_serializer(
            data=data, context={'request': request})
        self.serializer.is_valid(raise_exception=True)

        self.login()
        return self.get_response()


class PasswordChangeView(PasswordChangeView_):
    def post(self, request, *args, **kwargs):
        data = request.data.copy()

        if data:
            if 'old_password' in data:
                data['old_password'] = data['old_password'].lower()

            if 'new_password1' in data:
                data['new_password1'] = data['new_password1'].lower()

            if 'new_password2' in data:
                data['new_password2'] = data['new_password2'].lower()

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": _("New password has been saved.")})
