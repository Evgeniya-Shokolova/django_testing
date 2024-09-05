from datetime import datetime, timedelta

import pytest 
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from news.models import Comment, News

User = get_user_model()


@pytest.fixture
def creat_news():
    """Создаем набор новостей."""
    news = News.objects.create(title='Новость 1', text='Просто текст.')
    user = User.objects.create(username='Пользователь')

    return news, user


@pytest.fixture
def new_auth_client(creat_news, client):
    """Создаем авторизованный клиент."""
    news, user = creat_news
    client.force_login(user)
    return client, news


@pytest.fixture
def news_dates(creat_news):
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
def test_news():
    """Создаем одну тестовую новость."""
    return News.objects.create(title='Тестовая новость', text='Просто текст.')


@pytest.fixture
def comments_for_news(test_news):
    """Создаем набор комментариев для тестовой новости."""
    author = User.objects.create(username='Комментатор')
    now = timezone.now()
    Comment.objects.bulk_create([
        Comment(news=test_news, author=author, text=f'Tекст {index}', created=now + timedelta(days=index))
        for index in range(10)
    ])
    return Comment.objects.filter(news=test_news)


@pytest.fixture
def news():
    """Создаем объект новости перед тестами."""
    return News.objects.create(title='Заголовок', text='Текст')


@pytest.fixture
def author():
    """Создаем автора для тестов."""
    return User.objects.create_user(username='author', password='password')


@pytest.fixture
def reader():
    """Создаем читателя для тестов."""
    return User.objects.create_user(username='reader', password='password')


@pytest.fixture
def comment(news, author):
    """Создаем комментарий для тестов."""
    return Comment.objects.create(text='Текст комментария', news=news, author=author)


@pytest.fixture
def creat_news_auth_for_comments():
    """Создаем новость и пользователя для тестов комментариев."""
    news = News.objects.create(title='Заголовок', text='Текст')
    user = User.objects.create(username='Мимо Крокодил')
    return news, user


@pytest.fixture
def new_auth_and_comment():
    """Создаем новые пользователи и комментарий."""
    news = News.objects.create(title='Заголовок', text='Текст')
    author = User.objects.create(username='Автор комментария')
    comment = Comment.objects.create(
        news=news, author=author,
        text='Текст комментария')
    return author, comment, news
