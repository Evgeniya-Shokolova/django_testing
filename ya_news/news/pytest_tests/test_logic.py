from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from pytest_django.asserts import assertRedirects, assertFormError

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


User = get_user_model()

FORM_DATA = {'text': 'Текст комментария'}
NEW_COMMENT = {'text': 'Обновлённый комментарий'}


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, detail_url):
    """Проверка, что анонимный пользователь не может создать комментарий."""
    client.post(detail_url, data=FORM_DATA)
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_user_can_create_comment(auth_client, news, detail_url, author):
    """Проверка, что авторизованный пользователь может создать комментарий."""
    response = auth_client.post(detail_url, data=FORM_DATA)
    assertRedirects(response, f'{detail_url}#comments',
                    status_code=HTTPStatus.FOUND)
    comments_count = Comment.objects.count()
    assert comments_count == 1
    comment = Comment.objects.get()
    assert comment.text == FORM_DATA['text']
    assert comment.news == news
    assert comment.author == author


@pytest.mark.django_db
@pytest.mark.parametrize('bad_word', BAD_WORDS)
def test_user_cant_use_bad_words(auth_client, bad_word, detail_url):
    """Проверка, что пользователь не может использовать запрещенные слова."""
    bad_words_data = {'text': f'Просто текст, {bad_word}, еще текст'}
    response = auth_client.post(detail_url, data=bad_words_data)
    assert response.status_code == HTTPStatus.OK
    assertFormError(response, 'form', 'text', errors=WARNING)
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_author_can_delete_comment(auth_client, delete_url, detail_url):
    """Проверка, что автор комментария может его удалить."""
    response = auth_client.delete(delete_url)
    assertRedirects(response, f'{detail_url}#comments',
                    status_code=HTTPStatus.FOUND)
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_user_cant_delete_comment_of_another_user(auth_client, delete_url):
    """Пользователь не может удалить комментарий другого пользователя."""
    response = auth_client.delete(delete_url)
    assert response.status_code == HTTPStatus.FOUND
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_author_can_edit_comment(edit_url, create_comment,
                                 auth_client, detail_url):
    """Проверка, что автор комментария может его изменять."""
    comment = create_comment
    response = auth_client.post(edit_url, data=NEW_COMMENT)
    assertRedirects(response, f'{detail_url}#comments',
                    status_code=HTTPStatus.FOUND)
    updated_comment = Comment.objects.get(id=comment.id)
    assert updated_comment.text == NEW_COMMENT['text']
    assert updated_comment.news == comment.news
    assert updated_comment.author == comment.author


@pytest.mark.django_db
def test_user_cant_edit_comment_of_another_user(create_comment, auth_client,
                                                edit_url, reader):
    """Пользователь не может редактировать комментарий другого пользователя."""
    comment = create_comment
    auth_client.force_login(reader)
    response = auth_client.post(edit_url, data=NEW_COMMENT)
    assert response.status_code == HTTPStatus.NOT_FOUND
    unchanged_comment = Comment.objects.get(id=comment.id)
    assert unchanged_comment.text == comment.text
    assert unchanged_comment.news == comment.news
    assert unchanged_comment.author == comment.author
