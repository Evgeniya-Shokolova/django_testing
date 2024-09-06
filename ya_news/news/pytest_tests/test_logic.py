from http import HTTPStatus

import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse
from pytest_django.asserts import assertRedirects, assertFormError

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


User = get_user_model()

FORM_DATA = {'text': 'Текст комментария'}
NEW_COMMENT = {'text': 'Обновлённый комментарий'}


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(news, client):
    """Проверка, что анонимный пользователь не может создать комментарий."""
    url = reverse('news:detail', args=(news.id,))
    client.post(url, data=FORM_DATA)
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_user_can_create_comment(auth_client, news):
    """Проверка, что авторизованный пользователь может создать комментарий."""
    author = User.objects.create(username='Автор')
    auth_client.force_login(author)

    url = reverse('news:detail', args=[news.id])
    response = auth_client.post(url, data=FORM_DATA)

    assert response.status_code == HTTPStatus.FOUND
    assertRedirects(response, f'{url}#comments')
    comments_count = Comment.objects.count()
    assert comments_count == 1
    comment = Comment.objects.get()
    assert comment.text == FORM_DATA['text']
    assert comment.news == news
    assert comment.author == author


@pytest.mark.django_db
@pytest.mark.parametrize('bad_word', BAD_WORDS)
def test_user_cant_use_bad_words(auth_client, news, bad_word):
    """Проверка, что пользователь не может использовать запрещенные слова."""
    url = reverse('news:detail', args=(news.id,))
    bad_words_data = {'text': f'Просто текст, {bad_word}, еще текст'}

    response = auth_client.post(url, data=bad_words_data)
    assert response.status_code == HTTPStatus.OK
    assertFormError(response, 'form', 'text', errors=WARNING)
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_author_can_delete_comment(create_comment, auth_client):
    """Проверка, что автор комментария может его удалить."""
    comment = create_comment
    news = comment.news
    url_to_comments = reverse('news:detail', args=(news.id,)) + '#comments'
    delete_url = reverse('news:delete', args=(comment.id,))

    response = auth_client.delete(delete_url)
    assert response.status_code == HTTPStatus.FOUND
    assertRedirects(response, url_to_comments)

    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_user_cant_delete_comment_of_another_user(create_comment,
                                                  auth_client, reader):
    """Пользователь не может удалить комментарий другого пользователя."""
    comment = create_comment
    auth_client.force_login(reader)
    delete_url = reverse('news:delete', args=(comment.id,))

    response = auth_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND

    comments_count = Comment.objects.count()
    assert comments_count == 1


@pytest.mark.django_db
def test_author_can_edit_comment(create_comment, auth_client):
    """Проверка, что автор комментария может его изменять."""
    comment = create_comment
    news = comment.news
    edit_url = reverse('news:edit', args=(comment.id,))
    response = auth_client.post(edit_url, data=NEW_COMMENT)
    assert response.status_code == HTTPStatus.FOUND
    assertRedirects(response,
                    f'{reverse("news:detail", args=(news.id,))}#comments')
    updated_comment = Comment.objects.get(id=comment.id)
    assert updated_comment.text == NEW_COMMENT['text']
    assert updated_comment.news == news
    assert updated_comment.author == comment.author


@pytest.mark.django_db
def test_user_cant_edit_comment_of_another_user(create_comment, auth_client):
    """Пользователь не может редактировать комментарий другого пользователя."""
    comment = create_comment
    reader = User.objects.create(username='Читатель')

    auth_client.force_login(reader)
    edit_url = reverse('news:edit', args=(comment.id,))

    response = auth_client.post(edit_url, data=NEW_COMMENT)
    assert response.status_code == HTTPStatus.NOT_FOUND
    unchanged_comment = Comment.objects.get(id=comment.id)
    assert unchanged_comment.text == comment.text
    assert unchanged_comment.news == comment.news
    assert unchanged_comment.author == comment.author
