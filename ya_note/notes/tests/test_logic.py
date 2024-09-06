from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note


User = get_user_model()


class TestLogic(TestCase):
    def setUp(self):
        """Метод для инициализации данных для тестов."""
        self.author = User.objects.create(username='Автор')
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=self.author,
            slug='note-slug'
        )
        self.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug',
        }
        self.url_add = reverse('notes:add')
        self.login_url = reverse('users:login')
        self.not_author = User.objects.create(username='Не Автор')
        self.not_author_client = Client()
        self.not_author_client.force_login(self.not_author)

    def test_user_can_create_note(self):
        """Тест на создание заметки авторизованным пользователем."""
        Note.objects.all().delete()
        response = self.author_client.post(self.url_add, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.last()
        self.assertIsNotNone(new_note)
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])

    def test_anonymous_user_cant_create_note(self):
        """Тест на создание заметки анонимным пользователем."""
        current_count = Note.objects.count()
        response = self.client.post(self.url_add, data=self.form_data)
        expected_url = f'{self.login_url}?next={self.url_add}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), current_count)

    def test_not_unique_slug(self):
        url = reverse('notes:add')
        self.form_data['slug'] = self.note.slug
        response = self.author_client.post(url, data=self.form_data)

        self.assertFormError(response,
                             'form', 'slug', errors=(self.note.slug + WARNING))
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        """Тест на пустой слаг."""
        Note.objects.all().delete()
        self.form_data.pop('slug')
        response = self.author_client.post(self.url_add, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        current_count = Note.objects.count()
        self.assertEqual(current_count, 1)
        expected_slug = slugify(self.form_data['title'])
        new_note = Note.objects.get(title=self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        """Тест на редактирование заметки автором."""
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.author_client.post(url, self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self):
        """Тест на попытку редактирования заметки неавтором."""
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.not_author_client.post(url, self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)

    def test_author_can_delete_note(self):
        """Тест на удаление заметки автором."""
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.author_client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        """Тест на попытку удаления заметки неавтором."""
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.not_author_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
