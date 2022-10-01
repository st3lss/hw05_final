import shutil

import tempfile

from http import HTTPStatus

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post, User, Comment
from posts.forms import PostForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTests(TestCase):
    """Тестирование формы поста."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='forms_user')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Заголовок формы',
            slug='forms_group',
            description='Описание формы'
        )
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.user,
            image=cls.image,
            text='Текст формы'
        )
        cls.group_check = Group.objects.create(
            title='Тестирование формы',
            slug='forms_slug',
            description='Формы, формы'
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = self.client
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Проверка создания нового поста."""
        count_posts = Post.objects.count()
        first_post = Post.objects.first()
        context = {
            'group': self.group.id,
            'text': self.post.text,
            'image': self.post.image,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=context, follow=True)
        self.assertEqual(
            response.status_code, HTTPStatus.OK)
        self.assertEqual(
            first_post.text, context['text'])
        self.assertEqual(
            first_post.group_id, context['group'])
        self.assertEqual(
            first_post.image, context['image'])
        self.assertRedirects(
            response,
            reverse('posts:profile', args=[self.user]))
        self.assertEqual(Post.objects.count(), count_posts + 1)

    def test_edit(self):
        """Проверка редактирования."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'После ред',
            'group': self.group.pk,}
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id,}),
            data=form_data, follow=True)
        edited_post = Post.objects.get(id=self.post.id)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={
                'post_id': edited_post.id,}))
        self.assertEqual(
            edited_post.text, form_data['text'])
        self.assertEqual(
            edited_post.group.id, form_data['group'])
        self.assertEqual(Post.objects.count(), posts_count)

    def test_comment_add_post(self):
        """Проверка добавления коммента к посту."""
        Comment.objects.count()
        comment = {
            'author': self.user,
            'text': 'Коммент тест'
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=comment,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            args=(self.post.id,)))
        self.assertEqual(Comment.objects.count(), 1)
        self.assertTrue(Comment.objects.filter(
            text=comment['text'],
            author=comment['author']).exists())
        self.assertEqual(response.status_code, HTTPStatus.OK)
