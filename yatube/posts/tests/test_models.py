from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()
NUMBER = 15


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
        """Проверяем, что у моделей корректно работает __str__"""
        post = PostModelTest.post
        expected_object_name_post = post.text[:NUMBER]
        group = PostModelTest.group
        expected_object_name_group = group.title
        test_dict = {
            post: expected_object_name_post,
            group: expected_object_name_group,
        }
        for field, expected_value in test_dict.items():
            with self.subTest(field=field):
                self.assertEqual(
                    str(field), expected_value)
