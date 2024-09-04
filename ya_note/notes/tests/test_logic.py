from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from notes.forms import WARNING
from notes.models import Note
from pytils.translit import slugify


User = get_user_model()


class TestLogic(TestCase):
    @classmethod
    def setUp(cls):
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.not_author = User.objects.create(username='Не автор')
        cls.not_author_client = Client()
        cls.not_author_client.force_login(cls.not_author)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author,
            slug='note-slug'
        )
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'Новый-slug',
        }
        cls.url_add = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))

    def test_user_can_create_note(self):
        url = reverse('notes:add')
        response = self.author_client.post(url, data=self.form_data)

        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)

        new_note = Note.objects.get(title=self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        url = reverse('notes:add')
        response = self.client.post(url, data=self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'

        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 1)

    def test_not_unique_slug(self):
        url = reverse('notes:add')
        self.form_data['slug'] = self.note.slug
        response = self.author_client.post(url, data=self.form_data)

        self.assertFormError(response,
                             'form', 'slug', errors=(self.note.slug + WARNING))
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        url = reverse('notes:add')
        self.form_data.pop('slug')
        response = self.author_client.post(url, data=self.form_data)

        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2)

        new_note = Note.objects.get(title=self.form_data['title'])
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):

        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.author_client.post(url, self.form_data)

        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self):
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.not_author_client.post(url, self.form_data)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)

    def test_author_can_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.author_client.post(url)

        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.not_author_client.post(url)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
