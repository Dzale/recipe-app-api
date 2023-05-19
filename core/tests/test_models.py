from django import setup
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model

setup()

from core import models
from decimal import Decimal
from unittest.mock import patch


def create_user(email='user@example.com', password='test123'):
    return get_user_model().objects.create_user(
        email=email,
        password=password
    )


class ModelTests(TransactionTestCase):
    def test_create_user_with_email_should_succeed(self):
        email = 'test@example.com'
        password = '123456'
        user = create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_create_user_email_normalized(self):
        sample_emails = [
            [
                'test1@Example.com', 'test1@example.com'
            ],
            [
                'Test2@Example.com', 'Test2@example.com'
            ],
            [
                'TEST3@EXAMPLE.COM', 'TEST3@example.com'
            ],
            [
                'test4@example.COM', 'test4@example.com'
            ],
        ]

        for email, expected in sample_emails:
            user = create_user(email=email, password='test123')
            self.assertEqual(expected, user.email)

    def test_create_user_without_email_should_raise_error(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(email='', password='test123')

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser(
            email='test@example.com',
            password='test123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        user = create_user()

        recipe = models.Recipe.objects.create(
            user=user,
            title='Test recipe',
            time_minutes=5,
            price=Decimal('5.50'),
            description='Test recipe desc'
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        user = create_user()

        tag = models.Tag.objects.create(
            user=user,
            name='Test tag',
        )

        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        user = create_user()

        ingredient = models.Ingredient.objects.create(
            user=user,
            name='Test ingredient',
        )

        self.assertEqual(str(ingredient), ingredient.name)

    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test generating image path."""
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')
