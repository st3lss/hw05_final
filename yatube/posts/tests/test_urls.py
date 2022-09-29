from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, User


class PostsURLsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='No_Name')
        cls.user_next = User.objects.create(username='Some_Name')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='group_slug',
            description='Описание URL',)
        cls.post = Post.objects.create(
            id=1,
            group=cls.group,
            author=cls.user,
            text='Какой-то текст',)
        cls.URLPOST_CREATE = reverse('posts:post_create')
        cls.URLPOST_DETAIL = reverse('posts:post_detail', args=(cls.post.pk,))
        cls.URLPOST_EDIT = reverse('posts:post_edit', args=(cls.post.pk,))
        cls.url_status_code = (
            (reverse('posts:index'),
             [HTTPStatus.OK, 'posts/index.html']),
            (f'/group/{cls.post.group.slug}/',
             [HTTPStatus.OK, 'posts/group_list.html']),
            (f'/profile/{cls.user.username}/',
             [HTTPStatus.OK, 'posts/profile.html']),
            (cls.URLPOST_DETAIL,
             [HTTPStatus.OK, 'posts/post_detail.html']),
            (cls.URLPOST_EDIT,
             [HTTPStatus.FOUND, 'posts/create_post.html']),
            (cls.URLPOST_CREATE,
             [HTTPStatus.FOUND, 'posts/create_post.html']),
            (reverse('users:signup'),
             [HTTPStatus.OK, 'users/signup.html']),
            (reverse('users:login'),
             [HTTPStatus.OK, 'users/login.html']),
            (reverse('posts:follow_index'),
             [HTTPStatus.FOUND, 'posts/follow.html']),
            ('/some_page/',
             [HTTPStatus.NOT_FOUND, 'posts/404.html']),)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = self.client
        self.authorized_client.force_login(self.user)
        self.authorized_client_next = Client()
        self.authorized_client_next.force_login(self.user_next)
        cache.clear()

    def test_guest_client_correct_tatus_code(self):
        """Доступность для guest_client."""
        for url, code in self.url_status_code:
            with self.subTest(code=code):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, code[0])
        """Проверка соответствия шаблонов к их URL."""
        for address, template in self.url_status_code:
            with self.subTest(address=template):
                cache.clear()
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template[1])

    def test_post_create_exists_desired_location_authorized(self):
        """Доступность для authorized_client."""
        url_status_code = {self.URLPOST_EDIT: HTTPStatus.OK,
                           self.URLPOST_CREATE: HTTPStatus.OK}
        for url, code in url_status_code.items():
            with self.subTest(code=code):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, code)

    def test_post_create_redirect_anonymous_on_admin_login(self):
        """Редирект guest_client."""
        response = self.guest_client.get(self.URLPOST_CREATE, follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')
        """Редирект не автора поста со страницы редактирования."""
        response = self.authorized_client_next.get(
            self.URLPOST_EDIT, follow=True)
        self.assertRedirects(response, self.URLPOST_DETAIL)
