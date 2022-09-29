from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized_author = Client()
        cls.author = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='test_title',
            description='test_description',
            slug='testslug'
        )

    def setUp(self):
        for post_temp in range(13):
            Post.objects.create(
                text=f'text{post_temp}',
                author=self.author,
                group=self.group
            )

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
