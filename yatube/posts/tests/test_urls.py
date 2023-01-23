from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus
from django.core.cache import cache
from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост'
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.templates_url_names = {
            '': 'posts/index.html',
            '/follow/': 'posts/posts_follow.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
        }

    def test_urls_authorized_client(self):
        """Доступ авторизованного пользователя"""
        pages: tuple = ('/create/',
                        '/follow/',
                        f'/posts/{self.post.id}/edit/')
        for page in pages:
            response = self.guest_client.get(page)
            self.assertRedirects = (response, f'/auth/login/?next={page}')
        for page in pages:
            response = self.authorized_client.get(page)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_guest_client(self):
        """Доступ неавторизованного пользователя"""
        pages: tuple = ('/',
                        f'/group/{self.group.slug}/',
                        f'/profile/{self.user.username}/',
                        f'/posts/{self.post.id}/')
        for page in pages:
            response = self.guest_client.get(page)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_404(self):
        """Запрос несуществующей страницы"""
        response = self.guest_client.get('/test-no-popular', follow=True)
        error_name = 'Ошибка: unexisting_url не работает'
        self.assertEqual(response.status_code,
                         HTTPStatus.NOT_FOUND,
                         error_name)
