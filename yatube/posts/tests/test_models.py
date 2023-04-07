from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_group_verbose_names(self):
        """Проверяем работу поля verbose_name"""
        post = PostModelTest.post
        self.assertEqual(
            post._meta.get_field('group').verbose_name, 'Группа')

    def test_group_help_text(self):
        """Проверяем работу поля help_text"""
        post = PostModelTest.post
        self.assertEqual(
            post._meta.get_field('group').help_text,
            'Группы, к которой относится пост')
