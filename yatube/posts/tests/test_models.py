from django.test import TestCase

from ..models import Post, Group, User


class PostModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='models_group_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей Post и Group корректно
        работает __str__.
        """
        post = PostModelTests.post
        expected_post_str = post.text[:15]
        self.assertEqual(expected_post_str, str(post))

        group = PostModelTests.group
        expected_group_str = group.title
        self.assertEqual(expected_group_str, str(group))
