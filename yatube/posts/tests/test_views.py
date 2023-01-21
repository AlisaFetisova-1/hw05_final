import tempfile
import shutil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.models import Group, Post, User, Comment, Follow
from posts.forms import PostForm


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings (MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создание записи в БД"""
        super().setUpClass()
        cls.user = User.objects.create_user(username='authorized')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон"""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group',
                    kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username':
                            self.user.username}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            self.post.pk}): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            self.post.id}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            """типы полей формы в словаре context соответствуют ожиданиям"""
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_context_index(self):
        response = self.authorized_client.get(reverse('posts:index'))
        page_object = response.context['page_obj']
        self.assertEqual(len(page_object), 1)
        self.assertIsInstance(page_object[0], Post)

    def test_context_group_posts(self):
        response = self.authorized_client.get(
            reverse(
                'posts:group',
                kwargs={'slug': PostPagesTests.group.slug}
            )
        )
        page_object = response.context['page_obj']
        self.assertEqual(len(page_object), 1)
        self.assertIsInstance(page_object[0], Post)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': PostPagesTests.user}))
        self.assertEqual(response.context['page_obj'][0],
                         PostPagesTests.post)
        context_author = response.context.get('author')
        self.assertEqual(context_author, self.post.author)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post_text_0 = {response.context['post'].text: 'Тестовый пост',
                       response.context['post'].group: self.group,
                       response.context['post'].author: self.user.username}
        for value, expected in post_text_0.items():
            self.assertEqual(post_text_0[value], expected)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = testing_pages = (
            f'/posts/{PostPagesTests.post.pk}/edit/',
            '/create/',
        )
        for url in testing_pages:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertIsInstance(
                    response.context['form'],
                    PostForm
                )
                if 'edit' in url:
                    self.assertEqual(
                        response.context['is_edit'],
                        True
                    )
                    self.assertEqual(
                        response.context['post'],
                        PostPagesTests.post
                    )

    def test_paginator(self):
        bulk_posts = []
        for i in range(12):
            bulk_posts.append(Post(
                text=f'Тестовый пост {i}',
                author=PostPagesTests.user,
                group=PostPagesTests.group)
            )
        Post.objects.bulk_create(bulk_posts)

        reverse_name_posts = [
            reverse('posts:index'),
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}),
            reverse('posts:group',
                    kwargs={'slug': f'{self.group.slug}'}),
        ]

        for reverse_name in reverse_name_posts:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), 10,
                    'Количество постов на первой странице не равно десяти'
                )

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth1')
        cls.user2 = User.objects.create_user(username='auth2')

    def setUp(self):
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(title='Тестовая группа',
                                          slug='test_group')
        self.post = Post.objects.create(text='Тестовый текст',
                                        group=self.group,
                                        author=self.user,
                                        image=self.uploaded)


class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth1')
        cls.user2 = User.objects.create_user(username='auth2')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(title='Тестовая группа',
                                          slug='test_group')
        self.post = Post.objects.create(text='Тестовый текст',
                                        group=self.group,
                                        author=self.user)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с
           правильным контекстом комментария."""
        self.comment = Comment.objects.create(post_id=self.post.id,
                                              author=self.user,
                                              text='Тестовый коммент')
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        comments = {response.context['comments'][0].text: 'Тестовый коммент',
                    response.context['comments'][0].author: self.user.username
                    }
        for value, expected in comments.items():
            self.assertEqual(comments[value], expected)
            self.assertTrue(response.context['form'], 'форма получена')


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth1')
        cls.user2 = User.objects.create_user(username='auth2')
        cls.author = User.objects.create_user(username='someauthor')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(FollowViewsTest.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login( FollowViewsTest.user2)

    def test_user_follower_authors(self):
        '''Посты доступны подписчику'''
        count_follow = Follow.objects.filter(user=FollowViewsTest.user).count()
        data_follow = {'user': FollowViewsTest.user,
                       'author': FollowViewsTest.author}
        url_redirect = reverse(
            'posts:profile',
            kwargs={'username': FollowViewsTest.author.username})
        response = self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={
                'username': FollowViewsTest.author.username}),
            data=data_follow, follow=True)
        new_count_follow = Follow.objects.filter(
            user=FollowViewsTest.user).count()
        self.assertTrue(Follow.objects.filter(
                        user=FollowViewsTest.user,
                        author=FollowViewsTest.author).exists())
        self.assertRedirects(response, url_redirect)
        self.assertEqual(count_follow + 1, new_count_follow)

    def test_user_unfollower_authors(self):
        '''Посты не доступны не подписчику '''
        count_follow = Follow.objects.filter(
            user=FollowViewsTest.user).count()
        data_follow = {'user': FollowViewsTest.user,
                       'author': FollowViewsTest.author}
        url_redirect = ('/auth/login/?next=/profile/'
                        f'{self.author.username}/unfollow/')
        response = self.guest_client.post(
            reverse('posts:profile_unfollow', kwargs={
                'username': FollowViewsTest.author}),
            data=data_follow, follow=True)
        new_count_follow = Follow.objects.filter(
            user=FollowViewsTest.user).count()
        self.assertFalse(Follow.objects.filter(
            user=FollowViewsTest.user,
            author=FollowViewsTest.author).exists())
        self.assertRedirects(response, url_redirect)
        self.assertEqual(count_follow, new_count_follow)

    def test_follower_see_new_post(self):
        '''У подписчика появляется новый пост избранного автора.
           А у не подписчика его нет'''
        new_post_follower = Post.objects.create(
            author=FollowViewsTest.author,
            text='Текстовый текст')
        Follow.objects.create(user=FollowViewsTest.user,
                              author=FollowViewsTest.author)
        response_follower = self.authorized_client.get(
            reverse('posts:follow_index'))
        new_posts = response_follower.context['page_obj']
        self.assertIn(new_post_follower, new_posts)

    def test_unfollower_no_see_new_post(self):
        '''У не подписчика поста нет'''
        new_post_follower = Post.objects.create(
            author=FollowViewsTest.author,
            text='Текстовый текст')
        Follow.objects.create(user=FollowViewsTest.user,
                              author=FollowViewsTest.author)
        response_unfollower = self.authorized_client2.get(
            reverse('posts:follow_index'))
        new_post_unfollower = response_unfollower.context['page_obj']
        self.assertNotIn(new_post_follower, new_post_unfollower)