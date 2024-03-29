import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Post, Group

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая Группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        values_list = set(Post.objects.values_list('id', flat=True))
        form_data = {'text': 'Текст записанный в форму',
                     'group': self.group.id,
                     'image': uploaded, }
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )
        self.assertRedirects(
            response, reverse('posts:profile', kwargs={'username': 'auth'})
        )
        new_posts_collection = set(Post.objects.values_list('id', flat=True))
        new_ids_collection = new_posts_collection.difference(values_list)
        self.assertEqual(
            len(new_ids_collection),
            1
        )
        post = Post.objects.get(
            id=new_ids_collection.pop())
        self.assertEqual(form_data['group'], post.group.id)
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(self.user, post.author)
        self.assertEqual(f'posts/{form_data["image"].name}', post.image.name)

    def test_post_edit(self):
        """Валидная форма изменяет запись в Post."""
        form_data = {'text': 'Изменяем текст', 'group': PostFormTests.group.id}
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': self.post.id}))
        post = Post.objects.get(
            id=self.post.id,
        )
        self.assertEqual(form_data['group'], post.group.id)
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(post.author, self.post.author)

    def test_unauth_user_cant_publish_post(self):
        """Не авторизированный пользователь не может создать пост"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста',
            'group': self.group.id,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        redirect = reverse('login') + '?next=' + reverse('posts:post_create')
        self.assertRedirects(response, redirect)
        self.assertEqual(Post.objects.count(), posts_count)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая Группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            post_id=cls.post.id,
            author=cls.user,
            text='Комментарий к публикации',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_comment(self):
        """Валидная форма создает комментарий."""
        old_values_list = set(Comment.objects.values_list('id', flat=True))
        form_data = {'text': 'Тестируем комментарий к публикации',
                     }
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}
                    ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}
                    )
        )
        new_comments_collection = set(
            Comment.objects.values_list('id',
                                        flat=True
                                        )
        )
        new_ids_collection = new_comments_collection.difference(
            old_values_list
        )
        self.assertEqual(
            len(new_ids_collection),
            1
        )
        post_comment = Comment.objects.get(
            id=new_ids_collection.pop())
        self.assertEqual(form_data['text'], post_comment.text)
        self.assertEqual(self.user, post_comment.author)
        self.assertEqual(self.post.id, post_comment.post.id)
