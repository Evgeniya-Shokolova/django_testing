import pytest
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment, News

User = get_user_model()


@pytest.fixture
def news_setup(db):
    """Создаем новость и пользователя для тестов комментариев."""
    news = News.objects.create(title='Заголовок', text='Текст')
    user = User.objects.create(username='Мимо Крокодил')
    return news, user


@pytest.fixture
def auth_client(news_setup, client):
    """Создаем авторизованный клиент."""
    news, user = news_setup
    auth_client = client
    auth_client.force_login(user)
    return auth_client, news


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(news_setup, client):
    """Проверка, что анонимный пользователь не может создать комментарий."""
    news, _ = news_setup
    url = reverse('news:detail', args=(news.id,))
    form_data = {'text': 'Текст комментария'}

    client.post(url, data=form_data)
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_user_can_create_comment(auth_client):
    """Проверка, что авторизованный пользователь может создать комментарий."""
    client, news = auth_client
    user = client.get('/').wsgi_request.user

    url = reverse('news:detail', args=[news.id])
    form_data = {'text': 'Текст комментария'}

    response = client.post(url, data=form_data)

    assert response.status_code == HTTPStatus.FOUND
    assert response['Location'] == f'{url}#comments'

    comments_count = Comment.objects.count()
    assert comments_count == 1

    comment = Comment.objects.get()
    assert comment.text == 'Текст комментария'
    assert comment.news == news
    assert comment.author == user


@pytest.mark.django_db
def test_user_cant_use_bad_words(auth_client):
    """Проверка, что пользователь не может использовать запрещенные слова."""
    auth_client, news = auth_client
    url = reverse('news:detail', args=(news.id,))
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}

    response = auth_client.post(url, data=bad_words_data)
    assert response.status_code == HTTPStatus.OK
    assert response.context['form'].errors['text'] == [WARNING]

    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.fixture
def comment_setup(db):
    """Создаем новые пользователи и комментарий."""
    news = News.objects.create(title='Заголовок', text='Текст')
    author = User.objects.create(username='Автор комментария')
    comment = Comment.objects.create(
        news=news, author=author,
        text='Текст комментария')
    return author, comment, news


@pytest.mark.django_db
def test_author_can_delete_comment(comment_setup):
    """Проверка, что автор комментария может его удалить."""
    author, comment, news = comment_setup
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
def test_user_cant_delete_comment_of_another_user(comment_setup):
    """Пользователь не может удалить комментарий другого пользователя."""
    author, comment, news = comment_setup
    reader = User.objects.create(username='Читатель')

    client = Client()
    client.force_login(reader)
    delete_url = reverse('news:delete', args=(comment.id,))

    response = client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND

    comments_count = Comment.objects.count()
    assert comments_count == 1


@pytest.mark.django_db
def test_author_can_edit_comment(comment_setup):
    """Проверка, что автор комментария может его изменять."""
    author, comment, news = comment_setup
    edit_url = reverse('news:edit', args=(comment.id,))
    form_data = {'text': 'Обновлённый комментарий'}

    client = Client()
    client.force_login(author)

    response = client.post(edit_url, data=form_data)
    assert response.status_code == HTTPStatus.FOUND
    assert response[
        'Location'] == f'{reverse("news:detail",args=(news.id,))}#comments'

    comment.refresh_from_db()
    assert comment.text == 'Обновлённый комментарий'


@pytest.mark.django_db
def test_user_cant_edit_comment_of_another_user(comment_setup):
    """Пользователь не может редактировать комментарий другого пользователя."""
    author, comment, news = comment_setup
    reader = User.objects.create(username='Читатель')

    client = Client()
    client.force_login(reader)
    edit_url = reverse('news:edit', args=(comment.id,))
    form_data = {'text': 'Обновлённый комментарий'}

    response = client.post(edit_url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND

    comment.refresh_from_db()
    assert comment.text == 'Текст комментария'
