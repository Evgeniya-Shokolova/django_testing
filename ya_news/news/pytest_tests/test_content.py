from datetime import datetime, timedelta

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from news.forms import CommentForm
from news.models import Comment, News


User = get_user_model()


@pytest.fixture
def news_setup(db):
    """Создаем новости для теста главной страницы."""
    all_news = [
        News(title=f'Новость {index}', text='Просто текст.')
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ]
    News.objects.bulk_create(all_news)


@pytest.fixture
def news_with_dates(db):
    """Создаем новости с датами для теста порядка новостей."""
    today = datetime.today()
    all_news = [
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timedelta(days=index)
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ]
    News.objects.bulk_create(all_news)


@pytest.fixture
def detail_setup(db):
    """Создаем новость и комментарии для теста детальной страницы."""
    news = News.objects.create(
        title='Тестовая новость', text='Просто текст.'
    )
    author = User.objects.create(username='Комментатор')
    now = timezone.now()
    for index in range(10):
        comment = Comment.objects.create(
            news=news, author=author, text=f'Tекст {index}',
        )
        comment.created = now + timedelta(days=index)
        comment.save()
    return news


@pytest.mark.django_db
def test_home_news_count(client, news_setup):
    """Проверка количества новостей на главной странице."""
    home_url = reverse('news:home')
    response = client.get(home_url)
    object_list = response.context['object_list']
    news_count = object_list.count()
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_home_news_order(client, news_with_dates):
    """Проверка порядка новостей на главной странице."""
    home_url = reverse('news:home')
    response = client.get(home_url)
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_detail_comments_order(client, detail_setup):
    """Проверка порядка комментариев на детальной странице новостей."""
    detail_url = reverse('news:detail', args=(detail_setup.id,))
    response = client.get(detail_url)
    assert 'news' in response.context
    news = response.context['news']
    all_comments = news.comment_set.all()
    all_timestamps = [comment.created for comment in all_comments]
    sorted_timestamps = sorted(all_timestamps)
    assert all_timestamps == sorted_timestamps


@pytest.mark.django_db
def test_anonymous_client_has_no_form(client, detail_setup):
    """Проверка, что анонимный пользователь не видит форму комментария."""
    detail_url = reverse('news:detail', args=(detail_setup.id,))
    response = client.get(detail_url)
    assert 'form' not in response.context


@pytest.mark.django_db
def test_authorized_client_has_form(client, detail_setup):
    """Проверка, что авторизованный пользователь видит форму комментария."""
    author = User.objects.get(username='Комментатор')
    client.force_login(author)
    detail_url = reverse('news:detail', args=(detail_setup.id,))
    response = client.get(detail_url)
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
