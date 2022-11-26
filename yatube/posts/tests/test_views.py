from math import ceil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Comment, Group, Post
from posts.forms import PostForm


User = get_user_model()


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='HasNoName',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='test_slug',
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
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=uploaded,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def posts_check(self, post):
        """Проверка полей поста."""
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.group, self.post.group)
            self.assertEqual(post.author, self.post.author)

    def test_pages_show_correct_context(self):
        """Шаблон index, group, profile сформирован с правильным контекстом."""
        templates_pages_names = [
            reverse('posts:index'),
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}),
            reverse(
                'posts:profile', kwargs={'username': self.user}),
        ]
        for template in templates_pages_names:
            with self.subTest(template=template):
                response = self.authorized_client.get(template)
                self.posts_check(response.context['page_obj'][0])

    def test_groups_profile_show_correct_context(self):
        """Шаблоны group_list, profile сформированs с правильным контекстом."""
        templates_pages_names = [
            (reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}),
             self.group, 'group'),
            (reverse(
                'posts:profile',
                kwargs={'username': self.post.author.username}),
             self.post.author, 'author'),
        ]
        for reverse_name, fixtures, context in templates_pages_names:
            response = self.guest_client.get(reverse_name)
            self.assertEqual(fixtures, response.context[context])

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id})
        )
        self.posts_check(response.context['post'])

    def test_create_post_show_correct_context(self):
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
        self.assertIsInstance(response.context.get('form'), PostForm)
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


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='тестовое описание группы'
        )
        cls.TEST_OF_POST = 13
        posts_list = []
        for post_count in range(cls.TEST_OF_POST):
            posts_list.append(
                Post(
                    text=f'#{post_count} Тестовый текст .',
                    group=cls.group,
                    author=cls.user
                )
            )
        Post.objects.bulk_create(posts_list)

    def setUp(self):
        self.guest_client = Client()
        self.urls = (
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )

    def test_first_page_contains_ten_records(self):
        '''Паджинатор содержит 10 записей на первой странице'''
        for url in self.urls:
            response = self.guest_client.get(url)
            self.assertEqual(
                len(response.context['page_obj']),
                settings.COUNTER
            )

    def test_last_page_contains_three_records(self):
        '''Паджинатор содержит 3 записей на последней странице'''
        page_number = ceil(self.TEST_OF_POST / settings.COUNTER)
        for url in self.urls:
            response = self.guest_client.get(
                url + '?page=' + str(page_number)
            )
            self.assertEqual(
                len(response.context['page_obj']),
                (self.TEST_OF_POST - (
                    page_number - 1
                ) * settings.COUNTER)
            )


class CommentTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='comment')
        cls.post = Post.objects.create(
            text='Текст поста',
            author=cls.user,
        )
        cls.comment_url = reverse('posts:add_comment', args=['1'])

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_authorized_client_comment(self):
        """Авторизированный пользователь может комментировать"""
        text_comment = 'Kомментарий'
        self.authorized_client.post(self.comment_url,
                                    data={'text': text_comment}
                                    )
        comment = Comment.objects.get(id=self.post.id)
        self.assertEqual(comment.text, text_comment)
        self.assertEqual(Comment.objects.count(), 1)

    def test_guest_client_comment_redirect_login(self):
        """Неавторизированный пользователь не может комментаровать"""
        count_comments = Comment.objects.count()
        self.client.post(CommentTests.comment_url)
        self.assertEqual(count_comments, Comment.objects.count())


class TestCache(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='title',
            slug='slug',
            description='description'
        )
        cls.post = Post.objects.create(
            text='Текст поста',
            group=cls.group,
            author=cls.user,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(text='Текст поста',
                            author=self.user, )
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_autor = User.objects.create(username='autor')
        cls.post_follower = User.objects.create(username='follower')
        cls.post = Post.objects.create(text='Подпишись на меня',
                                       author=cls.post_autor, )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post_follower)
        self.follower_client = Client()
        self.follower_client.force_login(self.post_autor)
        cache.clear()

    def test_follow_on_user(self):
        """Проверка подписки на пользователя."""
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.post_follower}))
        follow = Follow.objects.all().latest('id')
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author_id, self.post_follower.id)
        self.assertEqual(follow.user_id, self.post_autor.id)

    def test_unfollow_on_user(self):
        """Проверка отписки от пользователя."""
        Follow.objects.create(user=self.post_autor,
                              author=self.post_follower)
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.post_follower}))
        self.assertEqual(Follow.objects.count(), count_follow - 1)

    def test_follow_on_authors(self):
        """Проверка записей у тех кто подписан."""
        post = Post.objects.create(author=self.post_autor,
                                   text="Подпишись на меня")
        Follow.objects.create(user=self.post_follower,
                              author=self.post_autor)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'].object_list)


def test_notfollow_on_authors(self):
    post = Post.objects.create(
        author=self.post_autor, text="Подпишись на меня")
    response = self.authorized_client.get(reverse('posts:follow_index'))
    self.assertNotIn(post, response.context['page_obj'].object_list)
