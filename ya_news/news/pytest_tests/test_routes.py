from http import HTTPStatus

import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse


User = get_user_model()


@pytest.mark.django_db
@pytest.mark.parametrize('url_name, args', [
    ('news:home', None),
    ('news:detail', pytest.lazy_fixture('parametrs_url')),
    ('users:login', None),
    ('users:logout', None),
    ('users:signup', None)
])
def test_pages_availability(client, url_name, args, news):
    """Проверка доступности страниц."""
    response = client.get(reverse(url_name, args=args))
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize("user_fixture, expected_status", [
    ('author', HTTPStatus.OK),
    ('reader', HTTPStatus.NOT_FOUND)
])
@pytest.mark.parametrize("name", ['news:edit', 'news:delete'])
def test_availability_for_comment_edit_and_delete(client, create_comment,
                                                  author, reader, user_fixture,
                                                  expected_status, name):

    user = locals()[user_fixture]
    client.force_login(user)
    comment = create_comment
    url = reverse(name, args=(comment.id,))
    response = client.get(url)
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize("name", ['news:edit', 'news:delete'])
def test_redirect_for_anonymous_client(client, create_comment, name):
    """Проверка редиректов для анонимных пользователей."""
    login_url = reverse('users:login')
    comment = create_comment
    url = reverse(name, args=(comment.id,))
    redirect_url = f'{login_url}?next={url}'
    response = client.get(url)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == redirect_url
