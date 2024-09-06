from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestContent(TestCase):

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
        test_cases = (
            (self.author_client, True),
            (self.not_author_client, False)
        )

        for client, expected in test_cases:
            for client, expected in test_cases:
                with self.subTest(client=client):
                    response = client.get(url)
                    object_list = response.context['object_list']
                    self.assertIs(
                        self.note in object_list,
                        expected
                    )

    def test_pages_contains_form(self):
        """Страницы содержат форму создания/редактирования заметки."""
        url_checks_form = [
            reverse('notes:add'),
            reverse('notes:edit', args=[self.note.slug]),
        ]

        for url in url_checks_form:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
