import pytest
from http import HTTPStatus
from django.urls import reverse
from django.contrib.auth import get_user_model

from news.models import News, Comment

User = get_user_model()


@pytest.fixture
def news():
    """Создаем объект новости перед тестами."""
    return News.objects.create(title='Заголовок', text='Текст')


@pytest.fixture
def author(db):
    """Создаем автора для тестов."""
    return User.objects.create_user(username='author', password='password')


@pytest.fixture
def reader(db):
    """Создаем читателя для тестов."""
    return User.objects.create_user(username='reader', password='password')


@pytest.fixture
def comment(news, author):
    """Создаем комментарий для тестов."""
    return Comment.objects.create(text='Текст комментария',
                                  news=news, author=author)


@pytest.mark.django_db
def test_pages_availability(client, news):
    """Проверка доступности страниц."""
    urls = (
        ('news:home', None),
        ('news:detail', (news.id,)),
        ('users:login', None),
        ('users:logout', None),
        ('users:signup', None),
    )
    for name, args in urls:
        url = reverse(name, args=args)
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_availability_for_comment_edit_and_delete(client,
                                                  comment,
                                                  author,
                                                  reader):
    """Проверка доступности страниц редактирования и удаления комментариев."""
    users_statuses = (
        (author, HTTPStatus.OK),
        (reader, HTTPStatus.NOT_FOUND),
    )

    for user, status in users_statuses:
        # Логиним пользователя в клиенте
        client.force_login(user)
        for name in ('news:edit', 'news:delete'):
            url = reverse(name, args=(comment.id,))
            response = client.get(url)
            assert response.status_code == status


@pytest.mark.django_db
def test_redirect_for_anonymous_client(client, comment):
    """Проверка редиректов для анонимных пользователей."""
    login_url = reverse('users:login')
    for name in ('news:edit', 'news:delete'):
        url = reverse(name, args=(comment.id,))
        redirect_url = f'{login_url}?next={url}'

        response = client.get(url)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == redirect_url
