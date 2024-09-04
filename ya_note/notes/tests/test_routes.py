from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from notes.models import Note
from django.contrib.auth import get_user_model

User = get_user_model()


class TestRoutes(TestCase):

    def setUp(self):
        self.client = Client()
        self.author = User.objects.create(username='Автор')
        self.not_author = User.objects.create(username='Не автор')
        self.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=self.author,
        )

    def test_pages_availability_for_anonymous_user(self):
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
        self.client.force_login(self.author)
        urls = [
            'notes:list',
            'notes:add',
            'notes:success'
        ]
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_non_authenticated_user(self):
        self.client.force_login(self.not_author)
        urls = [
            'notes:list',
            'notes:add',
            'notes:success'
        ]
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_different_users(self):
        cases = [
            (self.not_author, HTTPStatus.NOT_FOUND),
            (self.author, HTTPStatus.OK)
        ]
        for user, expected_status in cases:
            with self.subTest(user=user):
                self.client.force_login(user)
                urls = ['notes:detail', 'notes:edit', 'notes:delete']
                for name in urls:
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, expected_status)

    def test_redirects(self):
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
