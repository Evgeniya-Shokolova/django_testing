import pytest
from http import HTTPStatus
from django.urls import reverse
from django.contrib.auth import get_user_model


User = get_user_model()


@pytest.mark.django_db
@pytest.mark.parametrize('url_name, args', [
    ('news:home', None),
    ('news:detail', (1,)),
    ('users:login', None),
    ('users:logout', None),
    ('users:signup', None),])
def test_pages_availability(client, url_name, args, news):
    """Проверка доступности страниц."""
    if args is None:
        response = client.get(reverse(url_name))
    else:
        response = client.get(reverse(url_name, args=args))
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize("user, expected_status", [
    ('author', HTTPStatus.OK),
    ('reader', HTTPStatus.NOT_FOUND),
])
def test_availability_for_comment_edit_and_delete(client, comment,
                                                  author, reader, user,
                                                  expected_status):
    """Проверка доступности страниц редактирования и удаления комментариев."""
    client.force_login(locals()[user])

    for name in ('news:edit', 'news:delete'):
        url = reverse(name, args=(comment.id,))
        response = client.get(url)
        assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize("name", ['news:edit', 'news:delete'])
def test_redirect_for_anonymous_client(client, comment, name):
    """Проверка редиректов для анонимных пользователей."""
    login_url = reverse('users:login')
    url = reverse(name, args=(comment.id,))
    redirect_url = f'{login_url}?next={url}'

    response = client.get(url)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == redirect_url
