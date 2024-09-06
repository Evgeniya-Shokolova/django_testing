from datetime import datetime, timedelta

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
    return User.objects.create_user(username='author', password='password')


@pytest.fixture
def reader():
    """Создаем читателя для тестов."""
    return User.objects.create_user(username='reader', password='password')


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
def comments_for_news(news):
    """Создаем набор комментариев для тестовой новости."""
    author = User.objects.create(username='Комментатор')
    now = timezone.now()
    Comment.objects.bulk_create([
        Comment(news=news, author=author,
                text=f'Tекст {index}',
                created=now + timedelta(days=index))
        for index in range(10)
    ])
    return Comment.objects.filter(news=news)


@pytest.fixture
def detail_url(comments_for_news):
    """URL для детальной страницы новости."""
    news_id = comments_for_news.first().news.id
    return reverse('news:detail', args=(news_id,))


@pytest.fixture
def home_url():
    """URL для домашней страницы новостей."""
    return reverse('news:home')


@pytest.fixture
def news_dates():
    """Создаем новости с датами для теста порядка новостей."""
    today = datetime.today()
    return News.objects.bulk_create([
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timedelta(days=index)
        ) for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ])


@pytest.fixture
def parametrs_url(news):
    return (news.id,)
