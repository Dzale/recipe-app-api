from rest_framework import routers
from recipe.views import (RecipeViewSet, TagViewSet, IngredientViewSet)

router = routers.SimpleRouter()

router.register('recipes', RecipeViewSet)
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)
urlpatterns = router.urls
