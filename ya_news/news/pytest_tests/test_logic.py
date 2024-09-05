import pytest
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment

User = get_user_model()


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(creat_news_auth_for_comments,
                                            client):
    """Проверка, что анонимный пользователь не может создать комментарий."""
    news, _ = creat_news_auth_for_comments
    url = reverse('news:detail', args=(news.id,))
    form_data = {'text': 'Текст комментария'}

    client.post(url, data=form_data)
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_user_can_create_comment(new_auth_client):
    """Проверка, что авторизованный пользователь может создать комментарий."""
    client, news = new_auth_client
    user = client.get('/').context['user']

    url = reverse('news:detail', args=[news.id])
    form_data = {'text': 'Текст комментария'}

    response = client.post(url, data=form_data)

    assert response.status_code == HTTPStatus.FOUND
    assert response['Location'] == f'{url}#comments'
    comments_count = Comment.objects.count()
    assert comments_count == 1

    comment = Comment.objects.get()

    assert comment.text == form_data['text']

    assert comment.news == news
    assert comment.author == user


@pytest.mark.django_db
@pytest.mark.parametrize('bad_word', BAD_WORDS)
def test_user_cant_use_bad_words(new_auth_client, bad_word):
    """Проверка, что пользователь не может использовать запрещенные слова."""
    auth_client, news = new_auth_client
    url = reverse('news:detail', args=(news.id,))
    bad_words_data = {'text': f'Какой-то текст, {bad_word}, еще текст'}

    response = auth_client.post(url, data=bad_words_data)
    assert response.status_code == HTTPStatus.OK
    assert response.context['form'].errors['text'] == [WARNING]

    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_author_can_delete_comment(new_auth_and_comment):
    """Проверка, что автор комментария может его удалить."""
    author, comment, news = new_auth_and_comment
    url_to_comments = reverse('news:detail', args=(news.id,)) + '#comments'
    delete_url = reverse('news:delete', args=(comment.id,))

    client = Client()
    client.force_login(author)

    response = client.delete(delete_url)
    assert response.status_code == HTTPStatus.FOUND
    assert response['Location'] == url_to_comments

    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_user_cant_delete_comment_of_another_user(new_auth_and_comment):
    """Пользователь не может удалить комментарий другого пользователя."""
    author, comment, news = new_auth_and_comment
    reader = User.objects.create(username='Читатель')

    client = Client()
    client.force_login(reader)
    delete_url = reverse('news:delete', args=(comment.id,))

    response = client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND

    comments_count = Comment.objects.count()
    assert comments_count == 1


@pytest.mark.django_db
def test_author_can_edit_comment(new_auth_and_comment):
    """Проверка, что автор комментария может его изменять."""
    author, comment, news = new_auth_and_comment
    edit_url = reverse('news:edit', args=(comment.id,))
    form_data = {'text': 'Обновлённый комментарий'}

    client = Client()
    client.force_login(author)

    response = client.post(edit_url, data=form_data)
    assert response.status_code == HTTPStatus.FOUND
    assert response[
        'Location'] == f'{reverse("news:detail",args=(news.id,))}#comments'
    updated_comment = Comment.objects.get(id=comment.id)
    assert updated_comment.text == 'Обновлённый комментарий'
    assert updated_comment.news == news
    assert updated_comment.author == author
    assert updated_comment.created == comment.created


@pytest.mark.django_db
def test_user_cant_edit_comment_of_another_user(new_auth_and_comment):
    """Пользователь не может редактировать комментарий другого пользователя."""
    author, comment, news = new_auth_and_comment
    reader = User.objects.create(username='Читатель')

    client = Client()
    client.force_login(reader)
    edit_url = reverse('news:edit', args=(comment.id,))
    form_data = {'text': 'Обновлённый комментарий'}

    response = client.post(edit_url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    unchanged_comment = Comment.objects.get(id=comment.id)
    assert comment.text == 'Текст комментария'
    assert unchanged_comment.news == comment.news
    assert unchanged_comment.author == comment.author
    assert unchanged_comment.created == comment.created
