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
from django.utils.translation import ugettext_lazy as _


class Index(APIView):
    """
    Returns a description of the API
    """

    def get(self, request, format=None):
        return Response([{
            'name': 'Banned List',
            'description': 'Returns a filtered list of banned entities, request must be authenticated',
            'url': '/banned/<filter>'
        }, {
            'name': 'User List',
            'description': 'Returns a list of users, request must be from super user',
            'url': '/users/'
        }, {
            'name': 'User Detail',
            'description': 'Returns details from an user, request must be from that user or a superuser',
            'url': '/users/<id>'
        }])


class BannedList(generics.ListAPIView):
    serializer_class = BannedEntitySerializer

    def get_queryset(self):
        filter = self.request.data['filter'] if 'filter' in self.request.data else None
        return BannedEntity.objects.filter(  # pylint: disable=no-member
            Q(is_sactioned=True) &
            (
                Q(name__icontains=filter) |
                Q(program__icontains=filter) |
                Q(aliases__alias__icontains=filter)
            )
        ) if filter is not None else BannedEntity.objects.all()  # pylint: disable=no-member


class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class SignUpView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignupSerializer


class LoginView(LoginView_):
    def post(self, request, *args, **kwargs):
        self.request = request
        data = self.request.data
        if data and 'password' in data:
            data['password'] = data['password'].lower()

        self.serializer = self.get_serializer(
            data=data, context={'request': request})
        self.serializer.is_valid(raise_exception=True)

        self.login()
        return self.get_response()


class PasswordChangeView(PasswordChangeView_):
    def post(self, request, *args, **kwargs):
        data = request.data

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
