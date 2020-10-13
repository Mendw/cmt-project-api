from django.urls import path, include
from banned_list import views
from rest_framework.urlpatterns import format_suffix_patterns
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('banned/<str:filter>', views.BannedList.as_view()),
    path('banned/', views.BannedList.as_view()),
    path('users/', views.UserList.as_view()),
    path('user-details', views.UserDetail.as_view()),
    path('auth/login', views.LoginView.as_view()),
    path('auth/signup', views.RegisterView.as_view()),
    path('auth/logout', views.LogoutView.as_view()),
    path('auth/password-change', views.PasswordChangeView.as_view()),
    path('data-lists/', views.DataListView.as_view()),
    path('data-lists/<int:pk>', views.DataListDetailView.as_view()),
    path('parsers/', views.ParserListView.as_view()),
    path('refresh-database/', views.RefreshDatabase.as_view()),
    path('events/last', views.LastEventView.as_view()),
    path('events/', views.EventListView.as_view()),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns = format_suffix_patterns(urlpatterns)
