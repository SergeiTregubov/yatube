from math import ceil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Comment, Group, Post
from posts.forms import CommentForm, PostForm


User = get_user_model()


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.user_follower = User.objects.create_user(
            username='Follower'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
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
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.user,
            image=uploaded
        )

        Follow.objects.create(
            author=cls.user,
            user=cls.user_follower
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsTests.user)

    def test_index_group_profile_pages_show_correct_context(self):
        """Шаблон index, group, profile сформирован с правильным контекстом."""
        templates_pages_names = [
            reverse(
                'posts:index'
            ),
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile', kwargs={'username': self.post.author.username}
            ),
            reverse('posts:follow_index'),
        ]
        for template in templates_pages_names:
            self.authorized_client.force_login(self.user_follower)
            response = self.authorized_client.get(template)
            first_object = response.context['page_obj'][0]
            self.assertEqual(
                self.post.text,
                first_object.text
            )
            self.assertEqual(
                self.post.pub_date,
                first_object.pub_date
            )
            self.assertEqual(
                self.post.author.username,
                first_object.author.username
            )
            self.assertEqual(
                self.post.group.slug,
                first_object.group.slug
            )
            self.assertEqual(
                self.post.image,
                first_object.image
            )

    def test_group_profile_pages_show_correct_advanced_context(self):
        """Шаблоны group_list, profile сформированs с правильным контекстом."""
        templates_pages_names = [
            (reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
                self.post.group,
                'group',
            ),
            (reverse(
                'posts:profile',
                kwargs={'username': self.post.author.username}
            ),
                self.post.author,
                'author',
            ),
        ]
        for url, advanced_data, context_advanced_data in templates_pages_names:
            response = self.authorized_client.get(url)
            self.assertEqual(
                advanced_data,
                response.context[context_advanced_data]
            )

    def test_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.pk}
                    )
        )
        self.assertEqual(
            self.post.author.posts.count(),
            response.context['posts_count']
        )
        self.assertEqual(
            self.post.id,
            response.context['post'].id
        )
        self.assertEqual(
            self.post.text,
            response.context['post'].text
        )
        self.assertEqual(
            self.post.pub_date,
            response.context['post'].pub_date
        )
        self.assertEqual(
            self.post.author.username,
            response.context['post'].author.username
        )
        self.assertEqual(
            self.post.group.slug,
            response.context['post'].group.slug
        )
        self.assertEqual(
            self.post.image,
            response.context['post'].image
        )

    def test_create_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk}
                    )
        )
        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)
        self.assertEqual(response.context.get('form').instance, self.post)

    def test_post_not_get_another_group(self):
        """Созданный пост не попал в другую группу"""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test_slug'}
            )
        )
        post_object = response.context['page_obj']
        self.assertNotIn(self.post.group, post_object)

    def test_cache_context(self):
        '''Кэш записей index страницы сохранён'''
        old_data = self.authorized_client.get(
            reverse('posts:index')
        ).content
        Post.objects.filter(id=self.post.id).delete()
        new_data = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertEqual(new_data, old_data)
        cache.clear()
        after_clear_data = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertNotEqual(new_data, after_clear_data)

    def test_authorized_user_follow(self):
        """Авторизованный пользователь подписывается на других """
        url = reverse(
            'posts:profile_follow', kwargs={
                'username': self.user.username
            }
        )
        self.authorized_client.force_login(self.user_follower)
        response = self.authorized_client.get(url, follow=True)
        self.assertRedirects(
            response, reverse('posts:profile', kwargs={
                'username': self.user.username
            })
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_follower, author=self.user
            ).exists()
        )

    def test_authorized_user_unfollow(self):
        """Авторизованный пользователь отписывается от подписок"""
        url = reverse(
            'posts:profile_unfollow', kwargs={
                'username': self.user.username
            }
        )
        self.authorized_client.force_login(self.user_follower)
        response = self.authorized_client.get(url, follow=True)
        self.assertRedirects(
            response, reverse('posts:profile', kwargs={
                'username': self.user.username
            })
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_follower, author=self.user
            ).exists()
        )

    def test_new_post_in_page_follower_only(self):
        """Запись для подписчиков появляется только
        на странице подписчиков"""
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        first_object = response.context['page_obj']
        self.assertNotIn(self.post, first_object)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-group',
            description='test description',
        )
        cls.TEST_OF_POST: int = 13
        cls.post = [
            Post.objects.bulk_create([
                Post(
                    text='Тестовый текст' + str(post_plus),
                    group=cls.group,
                    author=cls.user,
                ),
            ])
            for post_plus in range(cls.TEST_OF_POST)
        ]
        cls.pages_names = (
            reverse('posts:index'),
            reverse(
                'posts:profile',
                kwargs={'username': cls.user}),
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug})
        )

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_contains_ten_posts(self):
        """Паджинатор содержит 10 записей на первой странице"""
        for url in self.pages_names:
            response = self.guest_client.get(url)
            self.assertEqual(
                len(response.context['page_obj']),
                settings.COUNTER
            )

    def test_last_page_contains_three_records(self):
        '''Паджинатор содержит 3 записи на последней странице'''
        page_number = ceil(self.TEST_OF_POST / settings.COUNTER)
        for url in self.pages_names:
            response = self.guest_client.get(
                url + '?page=' + str(page_number)
            )
            self.assertEqual(
                len(response.context['page_obj']),
                (self.TEST_OF_POST - (
                    page_number - 1
                ) * settings.COUNTER)
            )


class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Author')
        cls.user.notauthor = User.objects.create_user(username='notauthor')
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-group',
            description='test description'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.user
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user.notauthor)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным
        контекстом комментария другого пользователя."""
        self.comment = Comment.objects.create(
            post_id=self.post.id,
            author=self.user.notauthor,
            text='Тестируем комментарии'
        )
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(response.context['comments'][0], self.comment)
        self.assertIsInstance(response.context.get('form'), CommentForm)
