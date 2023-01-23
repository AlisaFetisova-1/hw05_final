import shutil
import tempfile
from http import HTTPStatus
from django.core.cache import cache
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile


from posts.models import Post, Group, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем тестовую группу
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_group",
            description="Описание",
        )
        # Создаем пользователя
        cls.user = User.objects.create_user(username="auth")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_create_post(self):
        '''Валидная форма создает новую запись в базе данных'''
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(name='small_2.gif',
                                           content=self.small_gif,
                                           content_type='image/gif')
        posts_count = Post.objects.count()
        form_data = {'text': 'Текст записанный в форму',
                     'group': self.group.id,
                     'image': self.uploaded
                     }
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data,
                                               follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(Post.objects.filter(text=form_data['text'],).exists())
        self.assertEqual(Post.objects.count(),
                         posts_count + 1,
                         )

    def test_edit_post(self):
        """ Валидная форма изменяет запись в Пост"""
        post = Post.objects.create(text='Тестовый текст',
                                   author=self.user,
                                   group=self.group)
        old_text = post
        group2 = Group.objects.create(title='Тестовая группа2',
                                      slug='tests-group',
                                      description='Описание')
        form_data = {'text': 'Текст записанный в форму',
                     'group': group2.id}
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': old_text.id}),
            data=form_data,
            follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(Post.objects.filter(text=form_data['text'],).exists())
        self.assertNotEqual(old_text.text, form_data['text'])
        self.assertNotEqual(old_text.group, form_data['group'])
        self.assertEqual(Post.objects.count(), posts_count,
                         'Число постов не должно меняться'
                         'при редактировании поста')


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем тестовую группу
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test_group",
            description="Тестовое описание",
        )
        cls.user = User.objects.create_user(username="Tester")
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test-group',
                                         description='Описание')
        cls.post = Post.objects.create(text='Тестовый текст',
                                       author=cls.user,
                                       group=cls.group)
        cls.comment = Comment.objects.create(post_id=cls.post.id,
                                             author=cls.user,
                                             text='Тестовый коммент')

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_comment(self):
        '''Проверка создания комментария'''
        comment_count = Comment.objects.count()
        form_data = {'post_id': self.post.id,
                     'text': 'Тестовый коммент2'}
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}),
            data=form_data, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(),
                         comment_count + 1,
                         )

    def test_no_edit_comment(self):
        '''Проверка запрета комментирования не авторизованого пользователя'''
        posts_count = Comment.objects.count()
        form_data = {'text': 'Тестовый коммент2'}
        response = self.guest_client.post(reverse('posts:add_comment',
                                          kwargs={'post_id': self.post.id}),
                                          data=form_data,
                                          follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(Comment.objects.count(),
                            posts_count + 1,
                            )

    def test_comment_null(self):
        '''Запрет пустого комментария'''
        posts_count = Comment.objects.count()
        form_data = {'text': ''}
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(Comment.objects.count(),
                            posts_count + 1,
                            )
