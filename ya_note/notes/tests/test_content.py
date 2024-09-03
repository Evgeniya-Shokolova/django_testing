import unittest
from django.urls import reverse
from django.test import Client
from notes.models import Note
from notes.forms import NoteForm
from django.contrib.auth import get_user_model

User = get_user_model()


class TestContent(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Автор')
        cls.not_author = User.objects.create(username='Не автор')

        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.not_author_client = Client()
        cls.not_author_client.force_login(cls.not_author)

        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,
        )

    def test_notes_list_for_different_users(self):
        """Заметка видна автору."""
        url = reverse('notes:list')

        """Проверка для автора"""
        response = self.author_client.get(url)
        object_list = response.context['object_list']
        self.assertIn(self.note, object_list)

        """Проверка для не автора"""
        response = self.not_author_client.get(url)
        object_list = response.context['object_list']
        self.assertNotIn(self.note, object_list)

    def test_pages_contains_form(self):
        """Страницы содержат форму создания/редактирования заметки."""
        url_create = reverse('notes:add')
        response_create = self.author_client.get(url_create)
        self.assertIn('form', response_create.context)
        self.assertIsInstance(response_create.context['form'], NoteForm)

        url_edit = reverse('notes:edit', args=[self.note.slug])
        response_edit = self.author_client.get(url_edit)
        self.assertIn('form', response_edit.context)
        self.assertIsInstance(response_edit.context['form'], NoteForm)
