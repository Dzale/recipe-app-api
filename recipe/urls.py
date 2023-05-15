from rest_framework import routers
from recipe.views import (RecipeViewSet)

router = routers.SimpleRouter()

router.register('recipes', RecipeViewSet)
urlpatterns = router.urls
