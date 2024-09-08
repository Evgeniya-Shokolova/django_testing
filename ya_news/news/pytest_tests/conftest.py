from datetime import timedelta

import pytest
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from news.models import Comment, News


User = get_user_model()


@pytest.fixture
def news():
    """Создаем одну тестовую новость."""
    return News.objects.create(title='Тестовая новость', text='Просто текст.')


@pytest.fixture
def author():
    """Создаем автора для тестов."""
    return User.objects.create_user(username='author',
                                    password='password')


@pytest.fixture
def reader():
    """Создаем читателя для тестов."""
    return User.objects.create_user(username='reader',
                                    password='password')


@pytest.fixture
def create_comment(news, author):
    """Создаем комментарий для тестов."""
    return Comment.objects.create(text='Текст комментария',
                                  news=news, author=author)


@pytest.fixture
def auth_client(client, author):
    """Создаем авторизованный клиент."""
    client.force_login(author)
    return client


@pytest.fixture
def comments_for_news(news, author):
    """Создаем набор комментариев для тестовой новости."""
    now = timezone.now()
    Comment.objects.bulk_create([
        Comment(news=news, author=author,
                text=f'Tекст {index}', created=now + timedelta(days=index))
        for index in range(10)
    ])


@pytest.fixture
def detail_url(news):
    """URL для детальной страницы новости."""
    return reverse('news:detail', args=(news.id,))


@pytest.fixture
def edit_url(create_comment):
    """URL для изменения комментария."""
    return reverse('news:edit', args=(create_comment.id,))


@pytest.fixture
def delete_url(create_comment):
    """URL для удаления комментария."""
    return reverse('news:delete', args=(create_comment.id,))


@pytest.fixture
def home_url():
    """URL для домашней страницы новостей."""
    return reverse('news:home')


@pytest.fixture
def news_dates():
    """Создаем новости с датами для теста порядка новостей."""
    today = timezone.now()
    News.objects.bulk_create([
        News(title=f'Новость {index}', text='Просто текст.',
             date=today - timedelta(days=index))
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ])


@pytest.fixture
def parametrs_url(news):
    """Параметры URL для тестирования с идентификатором новости."""
    return (news.id,)


@pytest.fixture
def auth_reader(client, reader):
    """Создаем авторизованный клиент для читателя."""
    client.force_login(reader)
    return client
