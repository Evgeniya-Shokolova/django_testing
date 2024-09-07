from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


User = get_user_model()


@pytest.mark.django_db
@pytest.mark.parametrize('name, args', [
    ('news:home', None),
    ('news:detail', pytest.lazy_fixture('parametrs_url')),
    ('users:login', None),
    ('users:logout', None),
    ('users:signup', None)
])
def test_pages_availability(client, name, args):
    """Проверка доступности страниц."""
    url = reverse(name, args=args)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize("client_fixture, expected_status", [
    (pytest.lazy_fixture('auth_client'), HTTPStatus.OK),
    (pytest.lazy_fixture('client'), HTTPStatus.FOUND)
])
@pytest.mark.parametrize("name", ['news:edit', 'news:delete'])
def test_availability_for_comment_edit_and_delete(client_fixture,
                                                  create_comment,
                                                  expected_status, name):
    """Проверка доступности страниц редактирования и удаления комментариев."""
    comment = create_comment
    url = reverse(name, args=(comment.id,))
    response = client_fixture.get(url)
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
