from django.urls import path, include
from banned_list import views
from rest_framework.urlpatterns import format_suffix_patterns
urlpatterns = [
    path('banned/<str:filter>', views.BannedList.as_view()),
    path('users/', views.UserList.as_view()),
    path('users/<int:pk>', views.UserDetail.as_view()),
    path('auth', views.LoginView.as_view()),
    path('auth/signup', views.SignUpView.as_view()),
    path('auth/logout', views.LogoutView.as_view()),
    path('auth/password-change', views.PasswordChangeView.as_view()),
    path('', views.Index.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
