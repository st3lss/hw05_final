from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, User


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='test_title',
            description='test_description',
            slug='testslug'
        )
        cls.posts = []

        for paginator_post in range(13):
            cls.posts.append(
                Post(
                    author=cls.author,
                    group=cls.group,
                    text=f'{paginator_post}',
                )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.user = User.objects.create_user(
            username='paginator_user'
        )
        self.authorized_author = self.client
        self.authorized_author.force_login(self.user)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """Проверка: на первой странице должно быть 10 постов."""
        templates_url_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html':
                reverse('posts:group_list', args=(self.group.slug,)),
            'posts/profile.html':
                reverse('posts:profile', args=(self.author,)),
        }
        for template, reverse_name in templates_url_names.items():
            with self.subTest(template=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), 10
                )

    def test_second_page_contains_ten_records(self):
        """Проверка: на второй странице должно быть 3 поста."""
        page_2 = '?page=2'
        templates_url_names = {
            'posts/index.html': reverse('posts:index') + page_2,
            'posts/group_list.html':
                reverse('posts:group_list', args=(self.group.slug,)) + page_2,
            'posts/profile.html':
                reverse('posts:profile', args=(self.author,)) + page_2,
        }
        for template, reverse_name in templates_url_names.items():
            with self.subTest(template=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), 3
                )
