import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from news.forms import CommentForm


User = get_user_model()


@pytest.mark.django_db
def test_home_news_count(client, news_dates):
    """Проверка количества новостей на главной странице."""
    home_url = reverse('news:home')
    response = client.get(home_url)
    object_list = response.context.get('object_list', [])
    news_count = len(object_list)
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_home_news_order(client, news_dates):
    """Проверка порядка новостей на главной странице."""
    home_url = reverse('news:home')
    response = client.get(home_url)
    object_list = response.context.get('object_list', [])
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_detail_comments_order(client, comments_for_news):
    """Проверка порядка комментариев на детальной странице новостей."""
    news_id = comments_for_news.first().news.id
    detail_url = reverse('news:detail', args=(news_id,))
    response = client.get(detail_url)

    assert 'news' in response.context
    news = response.context['news']
    all_comments = news.comment_set.all()
    all_timestamps = [comment.created for comment in all_comments]

    sorted_timestamps = sorted(all_timestamps)
    assert all_timestamps == sorted_timestamps


@pytest.mark.django_db
def test_anonymous_client_has_no_form(client, comments_for_news):
    """Проверка, что анонимный пользователь не видит форму комментария."""
    news_id = comments_for_news.first().news.id
    detail_url = reverse('news:detail', args=(news_id,))
    response = client.get(detail_url)

    assert 'form' not in response.context


@pytest.mark.django_db
def test_authorized_client_has_form(client, comments_for_news):
    """Проверка, что авторизованный пользователь видит форму комментария."""
    author = User.objects.get(username='Комментатор')
    client.force_login(author)

    news_id = comments_for_news.first().news.id
    detail_url = reverse('news:detail', args=(news_id,))
    response = client.get(detail_url)

    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
