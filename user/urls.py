from django.urls import path
from rest_framework import routers
from user.views import (UserViewSet, TokenViewSet)

router = routers.SimpleRouter()

router.register('users', UserViewSet)
urlpatterns = router.urls

urlpatterns += [
    path('tokens/', TokenViewSet.as_view(), name='token-list')
]
