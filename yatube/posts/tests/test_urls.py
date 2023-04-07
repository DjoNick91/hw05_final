from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from ..models import Post, Group
from http import HTTPStatus

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            id='1',
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_for_all(self):
        template_urls = {'': 200,
                         '/group/Тестовый слаг/': HTTPStatus.OK,
                         '/profile/TestUser/': HTTPStatus.OK,
                         '/posts/1/': HTTPStatus.OK,
                         }
        for template, code in template_urls.items():
            with self.subTest(url=template):
                response = self.guest_client.get(template)
                self.assertEqual(response.status_code, code)

    def test_url_for_autorized(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post(self):
        if self.authorized_client == self.post.author:
            response = self.authorized_client.get('/posts/1/edit/')
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/group/Тестовый слаг/': 'posts/group_list.html',
            '/profile/TestUser/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
