from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.no_author_of_post = User.objects.create_user(username='not_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.user)
        cache.clear()

    def test_urls_with_their_reverse_name_correct(self):
        """URL-адрес соответствует реверсу name"""
        test_pages = [
            ('/', reverse('posts:index'),),
            (f'/group/{self.post.group.slug}/',
                (reverse('posts:group_list',
                         kwargs={'slug': self.post.group.slug}
                         )
                 ),
             ),
            (f'/profile/{self.post.author.username}/',
                (reverse('posts:profile',
                         kwargs={'username': self.post.author.username}
                         )
                 ),
             ),
            (f'/posts/{self.post.id}/edit/',
                (reverse('posts:post_edit',
                         kwargs={'post_id': self.post.id}
                         )
                 ),
             ),
            (f'/posts/{self.post.id}/',
                (reverse('posts:post_detail',
                         kwargs={'post_id': self.post.id}
                         )
                 ),
             ),
            ('/create/', reverse('posts:post_create'),),
        ]
        for url, revers_data in test_pages:
            with self.subTest(url=url):
                self.assertEqual(url, revers_data)

    def test_home_url_exists_at_desired_location_authorized(self):
        """Страница доступна пользователю."""
        test_pages = [
            (reverse('posts:index'), HTTPStatus.OK, False,),
            (reverse(
                'posts:profile',
                kwargs={'username': self.post.author.username}
            ),
                HTTPStatus.OK,
                False,
            ),
            (reverse(
                'posts:group_list',
                kwargs={'slug': self.post.group.slug}
            ),
                HTTPStatus.OK,
                False,
            ),
            (reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            ),
                HTTPStatus.OK,
                False,
            ),
            (reverse('posts:post_create'), HTTPStatus.OK, True,),
            (reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ),
                HTTPStatus.OK,
                True,
            ),
            ('/unexisting-page/', HTTPStatus.NOT_FOUND, False,),
        ]
        for page, http_status, authorized_client in test_pages:
            with self.subTest(page=page):
                if authorized_client:
                    response = self.authorized_client.get(page)
                else:
                    response = self.guest_client.get(page, follow=True)
                self.assertEqual(response.status_code, http_status)

    def test_redirect_not_authorized(self):
        """Проверка перенаправления неавторизованного пользователя
        со страниц доступных только авторизованным"""
        test_pages = [
            (reverse('users:login')
                + '?next='
                + reverse('posts:post_edit',
                          kwargs={'post_id': self.post.id}
                          ),
                (reverse('posts:post_edit',
                         kwargs={'post_id': self.post.id}
                         )
                 ),
             ),
            (reverse('users:login')
                + '?next='
                + reverse('posts:post_create'),
                reverse('posts:post_create'),
             ),
        ]
        for redirect_address, expected_address in test_pages:
            with self.subTest(expected_address=expected_address):
                response = self.guest_client.get(expected_address, follow=True)
                self.assertRedirects(response, redirect_address)

    def test_edit_redirect(self):
        """Редактирование поста не автором"""
        self.authorized_client.force_login(self.no_author_of_post)
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}
                    ),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}
                    )
        )

    def test_urls_uses_correct_template_guest(self):
        """URL-адрес использует соответствующий шаблон."""
        test_pages = [
            (reverse('posts:index'), 'posts/index.html',),
            (reverse(
                'posts:profile',
                kwargs={'username': self.post.author.username}
            ),
                'posts/profile.html',
            ),
            (reverse(
                'posts:group_list',
                kwargs={'slug': self.post.group.slug}
            ),
                'posts/group_list.html',
            ),
            (reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            ),
                'posts/post_detail.html',
            ),
            (reverse(
                'posts:post_create'
            ),
                'posts/create_post.html',
            ),
            (reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ),
                'posts/create_post.html',
            ),
        ]
        for address, template in test_pages:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
