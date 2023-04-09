import tempfile
import shutil
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.models import Post, Group, Comment, Follow
from django.conf import settings
from django.core.cache import cache

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded
        )
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'Тестовый слаг'}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'TestUser'}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html'
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Шаблон index, group_list, profile с правильным контекстом."""
        names_pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'Тестовый слаг'}),
            reverse('posts:profile', kwargs={'username': 'TestUser'})
        ]
        for revers_name in names_pages:
            with self.subTest(revers_name=revers_name):
                response = self.guest_client.get(revers_name)
                first_obj = response.context['page_obj'][0]
                post_text_0 = first_obj.text
                post_author_0 = first_obj.author
                post_group_0 = first_obj.group.title
                post_image_0 = first_obj.image

                self.assertEqual(post_text_0, 'Тестовый пост')
                self.assertEqual(post_author_0.username, 'TestUser')
                self.assertEqual(post_group_0, 'Тестовая группа')
                self.assertEqual(post_image_0, self.post.image)

    def test_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_detail',
                                              kwargs={'post_id': self.post.id})
                                              )
        post_text = response.context['post'].text
        post_author = response.context['post'].author
        post_group = response.context['post'].group.title
        post_image = response.context['post'].image
        self.assertEqual(post_text, 'Тестовый пост')
        self.assertEqual(post_author.username, 'TestUser')
        self.assertEqual(post_group, 'Тестовая группа')
        self.assertEqual(post_image, self.post.image)

    def test_create_comment_autorized_only(self):
        """Комментарии может оставлять только авторизованный пользователь"""
        data_comment = {
            'post': self.post.id,
            'author': self.post.author.id,
            'text': 'Новый тестовый коммент',
        }
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=data_comment,
            follow=True
        )
        self.assertFalse(
            Comment.objects.filter(text='Новый тестовый коммент').exists()
        )

    def test_comment_created_on_post(self):
        """Комментарий появляется на странице поста"""
        data_comment = {
            'post': self.post.id,
            'author': self.post.author.id,
            'text': 'Новый тестовый коммент',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=data_comment,
            follow=True
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        comment = response.context['comments'][0]
        self.assertEqual(comment.text, 'Новый тестовый коммент')

    def test_post_create_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_edit',
                                              kwargs={'post_id': self.post.id})
                                              )
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_cache_index_page(self):
        """Проверка кеширования на главной странице"""
        Post.objects.create(
            author=self.user,
            text='Проверка кеширования',
        )
        response = self.authorized_client.get(reverse('posts:index'))
        before_delete_post = response.content
        Post.objects.filter(text='Проверка кеширования').delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(before_delete_post, response.content)

    def test_post_create_have_correct_view(self):
        """Пост корректно отображается на страницах сайта"""
        response_index = self.authorized_client.get(reverse('posts:index'))
        response_group = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug})
        )
        response_profile = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': 'TestUser'})
        )
        post = response_group.context['page_obj'][0]
        self.assertEqual(post.group, self.post.group)
        self.assertContains(response_group, self.post)
        self.assertContains(response_index, self.post)
        self.assertContains(response_profile, self.post)


CONTEXT = {
    reverse('posts:index'): 'index',
    reverse('posts:group_list',
            kwargs={'slug': 'Тестовый слаг'}): 'group_list',
    reverse('posts:profile', kwargs={'username': 'TestUser'}): 'profile',
}


class PaginatorViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        for i in range(15):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {i}',
                group=cls.group
            )

    def setUp(self):
        self.guest_client = Client()
        cache.clear()

    def test_first_page_contains_ten_records(self):
        for reverse_name, template in CONTEXT.items():
            with self.subTest(template=template):
                response = self.client.get(reverse_name)
                # Проверка: количество постов на первой странице равно 10.
                self.assertEqual(len(response.context.get('page_obj')), 10)

    def test_second_page_contains_five_records(self):
        for reverse_name, template in CONTEXT.items():
            with self.subTest(template=template):
                response = self.client.get(reverse_name + '?page=2')
                # Проверка: на второй странице должно быть 5 постов.
                self.assertEqual(len(response.context['page_obj']), 5)


class FollowingTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower = User.objects.create_user(username='follower')
        cls.author = User.objects.create_user(username='author')
        cls.not_follower = User.objects.create_user(username='not_follower')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост'
        )

    def setUp(self):
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)
        cache.clear()

    def test_follow_unfallow(self):
        """Проверка возможности подписки/отписки для авторизованного
        пользователя"""
        self.follower_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author.username}),
            follow=True,
        )
        self.assertTrue(
            Follow.objects.filter(user=self.follower,
                                  author=self.author).exists()
        )
        self.follower_client.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author.username}),
            follow=True
        )
        self.assertFalse(
            Follow.objects.filter(user=self.follower,
                                  author=self.author).exists()
        )

    def test_followers_see_post(self):
        """Подписчики видят посты авторов на которых подписаны"""
        Follow.objects.create(
            user=self.follower,
            author=self.author,
        )
        response = self.follower_client.get(
            reverse('posts:follow_index')
        )
        self.assertTrue(response.context.get('page_obj')[0].text,
                        'Тестовый пост')

    def test_not_followers_dont_see_post(self):
        not_follower_client = Client()
        not_follower_client.force_login(self.not_follower)
        response = not_follower_client.get(reverse('posts:follow_index'))
        self.assertFalse(response.context.get('post'))
