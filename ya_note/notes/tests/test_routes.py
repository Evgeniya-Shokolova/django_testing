from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestRoutes(TestCase):

    def setUp(self):
        """Создание необходимых объектов"""
        self.client_author = Client()
        self.client_not_author = Client()

        self.author = User.objects.create(username='Автор')
        self.not_author = User.objects.create(username='Не автор')

        self.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=self.author,
        )

        self.client_author.force_login(self.author)
        self.client_not_author.force_login(self.not_author)

    def tearDown(self):
        """Очищаем все заметки после каждого теста."""
        Note.objects.all().delete()

    def test_pages_availability_for_anonymous_user(self):
        """доступность страниц для анонимных пользователей"""
        urls = [
            'notes:home',
            'users:login',
            'users:logout',
            'users:signup'
        ]
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_authenticated_user(self):
        """доступность страниц для авторизованных пользователей."""
        urls = [
            'notes:list',
            'notes:add',
            'notes:success'
        ]
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client_author.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_non_authenticated_user(self):
        """доступность страниц для неавторизованного клиента"""
        urls = [
            'notes:list',
            'notes:add',
            'notes:success'
        ]
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client_not_author.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_different_users(self):
        """Доступность страниц для разных пользователей с различными правами"""
        cases = [
            (self.client_not_author, HTTPStatus.NOT_FOUND),
            (self.client_author, HTTPStatus.OK)
        ]
        urls = ['notes:detail', 'notes:edit', 'notes:delete']
        for client, expected_status in cases:
            for name in urls:
                with self.subTest(client=client, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = client.get(url)
                    self.assertEqual(response.status_code, expected_status)

    def test_redirects(self):
        """Не авторизованные пользователи перенаправляются на страницу входа"""
        login_url = reverse('users:login')
        urls = [
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:list', None),
        ]
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                expected_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, expected_url)
