from banned_list.models import BannedEntity, Alias, DataList, Parser, Event, RefreshToken, DatabaseStatus
from banned_list.serializers import BannedEntitySerializer, UserSerializer, DataListSerializer, ParserSerializer, DataListCreateUpdateSerializer, EventSerilizer
from rest_framework import generics
from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from banned_list.permissions import IsOwner
from rest_auth.views import (
    LoginView as LoginView_, LogoutView, PasswordChangeView as PasswordChangeView_
)
from rest_auth.registration.views import (
    RegisterView as RegisterView_
)
from rest_framework import status
from django.utils.translation import ugettext_lazy as _

from rest_framework.pagination import PageNumberPagination

from rest_framework.parsers import MultiPartParser, JSONParser
import requests

from google.cloud import tasks_v2                           # pylint: disable=import-error
from django.utils import timezone

import sys
import json

project = 'skilful-boulder-289120'
location = 'us-central1'
queue = 'refresh-queue'

client = tasks_v2.CloudTasksClient()
parent = client.queue_path(project, location, queue)


class QueriedPageNumberPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000


class BannedList(generics.ListAPIView):
    serializer_class = BannedEntitySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = QueriedPageNumberPagination

    def get_queryset(self):
        filter_ = None
        if 'filter' in self.kwargs:
            filter_ = self.kwargs['filter'].strip().split()
            filter_ = [f.strip() for f in filter_]
            filter_ = set([f for f in filter_ if f])

        result = BannedEntity.objects.all()                 # pylint: disable=no-member
        if filter_ != None:
            for f in filter_:
                result = result.filter(
                    Q(name__icontains=f) |
                    Q(name_unidecoded__icontains=f) |
                    Q(data_list__name__icontains=f) |
                    Q(aliases__alias__icontains=f) |
                    Q(aliases__alias_unidecoded__icontains=f)
                )
            return result.distinct()
        return result


class UserList(generics.ListAPIView):
    permission_classes = [IsAdminUser]

    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


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

    def get_response(self):
        serializer_class = self.get_response_serializer()

        serializer = serializer_class(instance=self.token,
                                      context={'request': self.request})
        data = serializer.data
        data['user'] = UserSerializer(self.user).data
        response = Response(data, status=status.HTTP_200_OK)

        return response

    def post(self, request, *args, **kwargs):
        self.request = request
        data = self.request.data.copy()
        if data and 'password' in data:
            data['password'] = data['password'].lower()

        self.serializer = self.get_serializer(
            data=data, context={'request': request})
        self.serializer.is_valid(raise_exception=True)

        self.login()
        response = self.get_response()

        if 'key' in response:
            response['user'] = UserSerializer(self.user).data

        return response


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


class DataListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser]
    queryset = DataList.objects.all()                       # pylint: disable=no-member
    serializer_class = DataListCreateUpdateSerializer

    def list(self, request, *args, **kwargs):
        self.serializer_class = DataListSerializer
        return super().list(request, *args, **kwargs)


class DataListDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser]
    queryset = DataList.objects.all()                       # pylint: disable=no-member
    serializer_class = DataListCreateUpdateSerializer


class ParserListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = ParserSerializer
    queryset = Parser.objects.filter(                       # pylint: disable=no-member
        Q(active=True) & (
            Q(datalist=None) | Q(reusable=True)
        )
    )


class EventListView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = EventSerilizer
    pagination_class = QueriedPageNumberPagination
    queryset = Event.objects.all()                          # pylint: disable=no-member


class RefreshDatabase(APIView):
    permission_classes = [IsAdminUser]

    def tasks_in_queue(self):
        response = client.list_tasks(parent=parent)

        total = len(response.tasks)
        while response.next_page_token:
            response = client.list_tasks(
                request={
                    'parent': parent,
                    'page_token': response.next_page_token
                }
            )

            total += len(response.tasks)

        return total

    def is_database_available(self):
        database = DatabaseStatus.objects.get(pk=1)              # pylint: disable=no-member

        if database.is_available:
            return True

        if self.tasks_in_queue() == 0:
            if database.locking_token != None and timezone.now() < database.locking_token.expiration:
                return False

            database.is_available = True
            database.save()
            return True

        return False

    def lock_database(self, token: RefreshToken):
        database = DatabaseStatus.objects.get(pk=1)                # pylint: disable=no-member

        database.is_available = False
        database.locking_token = token
        database.save()

    def check_lock(self, token: RefreshToken):
        database = DatabaseStatus.objects.get(pk=1)                    # pylint: disable=no-member

        if timezone.now() > token.expiration:
            return Response(status=401)
        if database.locking_token != token:
            return Response(status=403)

    def get(self, request):
        if not self.is_database_available():
            return Response("Database unavailable", status=503)

        client.purge_queue(name=parent)

        token = RefreshToken()
        token.save()

        self.lock_database(token)

        return Response({
            'token': token.token
        })

    def post(self, request: Request):
        token = request.data.get('token')

        try:
            token = RefreshToken.objects.get(               # pylint: disable=no-member
                token=token)
        except RefreshToken.DoesNotExist:                   # pylint: disable=no-member
            return Response(status=404)

        response = self.check_lock(token)
        if response:
            return response

        for data_list in DataList.objects.filter(parsed=False):       # pylint: disable=no-member
            task = {
                'app_engine_http_request': {
                    'http_method': tasks_v2.HttpMethod.POST,
                    'relative_uri': '/parse/',
                    'app_engine_routing': {
                        'service': 'tasks-handler'
                    },
                    'body': json.dumps({
                        'pk': data_list.pk
                    }).encode()
                }
            }
            client.create_task(parent=parent, task=task)

        RefreshToken.objects.filter(                        # pylint: disable=no-member
            expiration__lte=timezone.now()).delete()

        return Response()


class LastEventView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        first = Event.objects.first()                       # pylint: disable=no-member
        return Response(EventSerilizer(first).data if first is not None else {})
