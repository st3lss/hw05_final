import shutil

import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.forms import PostForm
from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='No_Name')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b')
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='group_slug',
            description='Тестовое описание')
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.user,
            image=cls.image,
            text='Какой-то текст',)

        cls.URL_INDEX = reverse('posts:index')
        cls.URL_POST_CREATE = reverse('posts:post_create')
        cls.URL_GROUP = reverse('posts:group_list', args=(cls.group.slug,))
        cls.URL_PROFILE = reverse('posts:profile', args=(cls.user,))
        cls.URL_POST_DETAIL = reverse('posts:post_detail', args=(cls.post.pk,))
        cls.URL_POST_EDIT = reverse('posts:post_edit', args=(cls.post.pk,))

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_page_show_correct_context(self):
        """Контексты для index, group_list, profile, post_detail."""
        url_code = {self.URL_INDEX, self.URL_GROUP,
                    self.URL_PROFILE, self.URL_POST_DETAIL}
        for url in url_code:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                if url == self.URL_POST_DETAIL:
                    first_object = response.context.get('post')
                else:
                    self.assertEqual(len(response.context['page_obj']), 1)
                    first_object = response.context.get('page_obj')[0]
                self.assertEqual(first_object.pk, self.post.pk)
                self.assertEqual(first_object.text, self.post.text)
                self.assertEqual(first_object.author, self.post.author)
                self.assertEqual(first_object.group.slug, self.group.slug)
                self.assertEqual(first_object.group.title, self.group.title)
                self.assertEqual(first_object.group.description,
                                 self.group.description)
                self.assertEqual(first_object.image, self.post.image)

    def test_posts_page_show_correct_context_create_edit(self):
        """Контексты для post_create, post_edit."""
        urls = {self.URL_POST_CREATE, self.URL_POST_EDIT}
        for url in urls:
            response = self.authorized_client.get(url)
            form_fields = {'text', 'post', 'is_edit'}
            for value in form_fields:
                with self.subTest(value=value):
                    form_field = response.context.get('form')
                    self.assertIsInstance(form_field, PostForm)

    def test_cache_indx(self):
        """Проверка кэширования индекс."""
        post_cach = self.authorized_client.get(reverse('posts:index')).content
        Post.objects.create(
            text='Пост кэш',
            author=self.user,
        )
        post_1 = self.authorized_client.get(reverse('posts:index')).content
        self.assertEqual(post_cach, post_1)
        cache.clear()
        post_2 = self.authorized_client.get(reverse('posts:index')).content
        self.assertNotEqual(post_cach, post_2)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username='posts_author',)
        cls.follower = User.objects.create(
            username='follower',)
        cls.post = Post.objects.create(
            author=FollowViewsTest.author,
            text='Какой-то текст',)

    def setUp(self):
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_follow_page(self):
        """Проверка подписки/отписки."""
        self.follower_client.get(reverse('posts:profile_follow',
                                 kwargs={'username': self.author.username}))
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual((len(response.context['page_obj'])), 1)
        page_object = response.context.get('page_obj').object_list[0]
        self.assertEqual(page_object.author, self.author)
        self.assertEqual(page_object.text, self.post.text)
        self.assertEqual(page_object.pub_date, self.post.pub_date)
        
        self.follower_client.get(reverse('posts:profile_unfollow',
                                 kwargs={'username': self.author.username}))
        response = self.follower_client.get(reverse('posts:follow_index'))
        page_object = response.context.get('page_obj').object_list
        self.assertEqual((len(page_object)), 0)

    def test_cant_following_myself(self):
        """Нельзя подписаться на себя."""
        response = self.author_client.get(reverse('posts:follow_index'))
        page_object = response.context.get('page_obj').object_list
        self.assertEqual((len(page_object)), 0)
        self.author_client.get(
            reverse('posts:profile_follow',
                    kwargs={
                        'username': self.author.username}))
        response = self.author_client.get(reverse('posts:follow_index'))
        self.assertEqual((len(page_object)), 0)
