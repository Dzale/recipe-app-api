from rest_framework import routers
from recipe.views import (RecipeViewSet, TagViewSet)

router = routers.SimpleRouter()

router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)
urlpatterns = router.urls
