from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import LoginPVDView

app_name = 'usuarios'

urlpatterns = [
    path('login/', LoginPVDView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]