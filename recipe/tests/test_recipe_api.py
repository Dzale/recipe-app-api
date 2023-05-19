from django import setup

setup()

from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

from core.models import Recipe, Tag, Ingredient
import tempfile
import os
from PIL import Image

RECIPES_URL = reverse('recipe-list')


def detail_url(recipe_id):
    return reverse('recipe-detail', args=[recipe_id])


def create_tag(user, **params):
    defaults = {
        'name': 'Test name',
    }
    defaults.update(params)
    return Tag.objects.create(user=user, **defaults)


def create_ingredient(user, **params):
    defaults = {
        'name': 'Test name',
    }
    defaults.update(params)
    return Ingredient.objects.create(user=user, **defaults)


def image_upload_url(recipe_id):
    return reverse('recipe-upload-image', args=[recipe_id])


def create_recipe(user, **params):
    defaults = {
        'title': 'Test title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Test desc'
    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TransactionTestCase):

    def setUp(self) -> None:
        self.client = APIClient()

    def test_without_auth_should_return_401(self):
        res = self.client.get(RECIPES_URL)

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, res.status_code)


class PrivateRecipeApiTests(TransactionTestCase):

    def setUp(self) -> None:
        payload = {
            'email': 'test@example.com',
            'password': 'test123',
            'name': 'Test name'
        }
        self.user = get_user_model().objects.create_user(**payload)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipes_should_return_200(self):
        payload = {
            'email': 'test123@example.com',
            'password': 'test123',
            'name': 'Test name2'
        }
        other_user = get_user_model().objects.create_user(**payload)
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        create_recipe(user=other_user)
        create_recipe(user=other_user)

        res = self.client.get(RECIPES_URL)
        self.assertEqual(status.HTTP_200_OK, res.status_code)

        recipes = Recipe.objects.filter(user=self.user).order_by('-id')
        serialize = RecipeSerializer(recipes, many=True)
        self.assertEqual(2, len(res.data))
        self.assertEqual(res.data, serialize.data)

    def test_retrieve_recipes_filter_by_tags_should_return_200(self):
        r1 = create_recipe(user=self.user, title='R1')
        r2 = create_recipe(user=self.user, title='R2')
        t1 = create_tag(user=self.user, name='T1')
        t2 = create_tag(user=self.user, name='T2')
        r1.tags.add(t1)
        r2.tags.add(t1)

        r3 = create_recipe(user=self.user, title='R3')

        params = {'tags': f'{t1.id},{t2.id}'}
        res = self.client.get(RECIPES_URL, params)
        self.assertEqual(status.HTTP_200_OK, res.status_code)
        self.assertEqual(2, len(res.data))

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_retrieve_recipes_filter_by_ingredients_should_return_200(self):
        r1 = create_recipe(user=self.user, title='R1')
        r2 = create_recipe(user=self.user, title='R2')
        i1 = create_ingredient(user=self.user, name='I1')
        i2 = create_ingredient(user=self.user, name='I2')
        r1.ingredients.add(i1)
        r2.ingredients.add(i1)

        r3 = create_recipe(user=self.user, title='R3')

        params = {'ingredients': f'{i1.id},{i2.id}'}
        res = self.client.get(RECIPES_URL, params)
        self.assertEqual(status.HTTP_200_OK, res.status_code)
        self.assertEqual(2, len(res.data))

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_get_recipe_details_should_return_200(self):
        recipe = create_recipe(user=self.user)

        res = self.client.get(detail_url(recipe.id))
        self.assertEqual(status.HTTP_200_OK, res.status_code)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe_should_return_201(self):
        payload = {
            'title': 'Test title',
            'time_minutes': 22,
            'price': Decimal('5.25'),
            'description': 'Test desc'
        }
        self.assertEqual(0, Recipe.objects.count())
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(1, Recipe.objects.count())

        self.assertEqual(status.HTTP_201_CREATED, res.status_code)

        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(self.user, recipe.user)

    def test_recipe_partial_update_should_return_200(self):
        recipe = create_recipe(user=self.user)
        payload = {
            'title': 'Updated title',
        }
        self.assertEqual(1, Recipe.objects.count())
        res = self.client.patch(detail_url(recipe.id), payload)
        self.assertEqual(1, Recipe.objects.count())

        self.assertEqual(status.HTTP_200_OK, res.status_code)

        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(self.user, recipe.user)

    def test_recipe_update_should_return_200(self):
        recipe = create_recipe(user=self.user)
        payload = {
            'title': 'Updated title',
            'time_minutes': 222,
            'price': Decimal('52.25'),
            'description': 'Updated desc'
        }
        self.assertEqual(1, Recipe.objects.count())
        res = self.client.put(detail_url(recipe.id), payload)
        self.assertEqual(1, Recipe.objects.count())

        self.assertEqual(status.HTTP_200_OK, res.status_code)

        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(self.user, recipe.user)

    def test_recipe_partial_update_with_new_user_should_return_400(self):
        payload = {
            'email': 'test123@example.com',
            'password': 'test123',
            'name': 'Test name2'
        }
        other_user = get_user_model().objects.create_user(**payload)
        recipe = create_recipe(user=self.user)
        payload = {
            'user': other_user.id,
        }

        self.client.patch(detail_url(recipe.id), payload)

        recipe.refresh_from_db()
        self.assertEqual(self.user, recipe.user)

    def test_recipe_delete_should_return_200(self):
        recipe = create_recipe(user=self.user)

        self.assertEqual(1, Recipe.objects.count())
        res = self.client.delete(detail_url(recipe.id))
        self.assertEqual(0, Recipe.objects.count())

        self.assertEqual(status.HTTP_204_NO_CONTENT, res.status_code)

    def test_recipe_delete_from_other_user_should_return_404(self):
        payload = {
            'email': 'test123@example.com',
            'password': 'test123',
            'name': 'Test name2'
        }
        other_user = get_user_model().objects.create_user(**payload)
        recipe = create_recipe(user=other_user)

        self.assertEqual(1, Recipe.objects.count())
        res = self.client.delete(detail_url(recipe.id))
        self.assertEqual(1, Recipe.objects.count())

        self.assertEqual(status.HTTP_404_NOT_FOUND, res.status_code)

    def test_create_recipe_with_new_tags_should_return_201(self):
        payload = {
            'title': 'Test title',
            'time_minutes': 22,
            'price': Decimal('5.25'),
            'description': 'Test desc',
            'tags': [
                {
                    'name': 'Tag 1'
                },
                {
                    'name': 'Tag 2'
                },
            ]
        }
        self.assertEqual(0, Recipe.objects.count())
        self.assertEqual(0, Tag.objects.count())
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(1, Recipe.objects.count())
        self.assertEqual(2, Tag.objects.count())

        self.assertEqual(status.HTTP_201_CREATED, res.status_code)

    def test_create_recipe_with_existing_tags_should_return_201(self):
        create_tag(user=self.user, name='Tag 1')
        payload = {
            'title': 'Test title',
            'time_minutes': 22,
            'price': Decimal('5.25'),
            'description': 'Test desc',
            'tags': [
                {
                    'name': 'Tag 1'
                },
                {
                    'name': 'Tag 2'
                },
            ]
        }
        self.assertEqual(0, Recipe.objects.count())
        self.assertEqual(1, Tag.objects.count())
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(1, Recipe.objects.count())
        self.assertEqual(2, Tag.objects.count())

        self.assertEqual(status.HTTP_201_CREATED, res.status_code)

    def test_update_recipe_with_existing_tags_should_return_200(self):
        create_tag(user=self.user, name='Tag 1')
        recipe = create_recipe(user=self.user)
        payload = {
            'tags': [
                {
                    'name': 'Tag 1'
                },
            ]
        }
        self.assertEqual(1, Recipe.objects.count())
        self.assertEqual(1, Tag.objects.count())
        res = self.client.patch(detail_url(recipe.id), payload, format='json')
        self.assertEqual(1, Recipe.objects.count())
        self.assertEqual(1, Tag.objects.count())

        self.assertEqual(status.HTTP_200_OK, res.status_code)

        recipe = Recipe.objects.get(id=res.data['id'])
        self.assertEqual(1, recipe.tags.count())

    def test_update_recipe_without_tags_should_return_200(self):
        tag = create_tag(user=self.user, name='Tag 1')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)
        payload = {
            'tags': []
        }
        self.assertEqual(1, Recipe.objects.count())
        self.assertEqual(1, Tag.objects.count())
        res = self.client.patch(detail_url(recipe.id), payload, format='json')
        self.assertEqual(1, Recipe.objects.count())
        self.assertEqual(1, Tag.objects.count())

        self.assertEqual(status.HTTP_200_OK, res.status_code)

        recipe = Recipe.objects.get(id=res.data['id'])
        self.assertEqual(0, recipe.tags.count())

    def test_create_recipe_with_new_ingredients_should_return_201(self):
        payload = {
            'title': 'Test title',
            'time_minutes': 22,
            'price': Decimal('5.25'),
            'description': 'Test desc',
            'ingredients': [
                {
                    'name': 'Ingredient 1'
                },
                {
                    'name': 'Ingredient 2'
                },
            ]
        }
        self.assertEqual(0, Recipe.objects.count())
        self.assertEqual(0, Ingredient.objects.count())
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(1, Recipe.objects.count())
        self.assertEqual(2, Ingredient.objects.count())

        self.assertEqual(status.HTTP_201_CREATED, res.status_code)

    def test_create_recipe_with_existing_ingredients_should_return_201(self):
        create_ingredient(user=self.user, name='Ingredient 1')
        payload = {
            'title': 'Test title',
            'time_minutes': 22,
            'price': Decimal('5.25'),
            'description': 'Test desc',
            'ingredients': [
                {
                    'name': 'Ingredient 1'
                },
                {
                    'name': 'Ingredient 2'
                },
            ]
        }
        self.assertEqual(0, Recipe.objects.count())
        self.assertEqual(1, Ingredient.objects.count())
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(1, Recipe.objects.count())
        self.assertEqual(2, Ingredient.objects.count())

        self.assertEqual(status.HTTP_201_CREATED, res.status_code)

    def test_update_recipe_with_new_ingredients_should_return_200(self):
        recipe = create_recipe(user=self.user)
        payload = {
            'ingredients': [
                {
                    'name': 'Ingredient 1'
                },
            ]
        }
        self.assertEqual(1, Recipe.objects.count())
        self.assertEqual(0, Ingredient.objects.count())
        res = self.client.patch(detail_url(recipe.id), payload, format='json')
        self.assertEqual(1, Recipe.objects.count())
        self.assertEqual(1, Ingredient.objects.count())

        self.assertEqual(status.HTTP_200_OK, res.status_code)

        recipe = Recipe.objects.get(id=res.data['id'])
        self.assertEqual(1, recipe.ingredients.count())

    def test_update_recipe_with_existing_ingredients_should_return_200(self):
        create_ingredient(user=self.user, name='Ingredient 1')
        recipe = create_recipe(user=self.user)
        payload = {
            'ingredients': [
                {
                    'name': 'Ingredient 1'
                },
            ]
        }
        self.assertEqual(1, Recipe.objects.count())
        self.assertEqual(1, Ingredient.objects.count())
        res = self.client.patch(detail_url(recipe.id), payload, format='json')
        self.assertEqual(1, Recipe.objects.count())
        self.assertEqual(1, Ingredient.objects.count())

        self.assertEqual(status.HTTP_200_OK, res.status_code)

        recipe = Recipe.objects.get(id=res.data['id'])
        self.assertEqual(1, recipe.ingredients.count())

    def test_update_recipe_without_ingredients_should_return_200(self):
        ingredient = create_ingredient(user=self.user, name='Ingredient 1')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)
        payload = {
            'ingredients': []
        }
        self.assertEqual(1, Recipe.objects.count())
        self.assertEqual(1, Ingredient.objects.count())
        res = self.client.patch(detail_url(recipe.id), payload, format='json')
        self.assertEqual(1, Recipe.objects.count())
        self.assertEqual(1, Ingredient.objects.count())

        self.assertEqual(status.HTTP_200_OK, res.status_code)

        recipe = Recipe.objects.get(id=res.data['id'])
        self.assertEqual(0, recipe.ingredients.count())


class ImageUploadTests(TransactionTestCase):
    def setUp(self) -> None:
        payload = {
            'email': 'test@example.com',
            'password': 'test123',
            'name': 'Test name'
        }
        self.user = get_user_model().objects.create_user(**payload)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self) -> None:
        self.recipe.image.delete()

    def test_upload_image_should_return_200(self):
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image', image_file}
            res = self.client.post(url, payload, format='multipart')
            self.assertEqual(status.HTTP_200_OK, res.status_code)

        self.recipe.refresh_from_db()
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_with_invalid_image_should_return_400(self):
        url = image_upload_url(self.recipe.id)
        payload = {'image', 'notanimage'}
        res = self.client.post(url, payload, format='multipart')
        self.assertEqual(status.HTTP_400_BAD_REQUEST, res.status_code)
