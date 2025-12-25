from http import HTTPStatus

import pytest


@pytest.mark.django_db
@pytest.mark.parametrize(
    'url, http_method, parametrized_client, status',
    (
        ('courses', 'get', 'client', HTTPStatus.OK),
        ('courses', 'post', 'client', HTTPStatus.UNAUTHORIZED),
        ('lessons', 'get', 'client', HTTPStatus.UNAUTHORIZED),
        ('groups', 'get', 'client', HTTPStatus.UNAUTHORIZED),
        ('pay', 'get', 'client', HTTPStatus.UNAUTHORIZED),
        ('courses', 'get', 'user_client', HTTPStatus.OK),
        ('courses', 'post', 'user_client', HTTPStatus.FORBIDDEN),
        ('lessons', 'get', 'user_client', HTTPStatus.FORBIDDEN),
        ('lessons', 'post', 'user_client', HTTPStatus.FORBIDDEN),
        ('groups', 'get', 'user_client', HTTPStatus.FORBIDDEN),
        ('pay', 'post', 'user_client', HTTPStatus.CREATED),
    ),
)
def test_courses_availability_for_anonymous_and_other_user(
    get_url,
    request,
    url,
    http_method,
    parametrized_client,
    status
):
    """Проверяет доступность для анонимных пользователей и других."""
    client = request.getfixturevalue(parametrized_client)
    url = get_url[url]
    response = getattr(client, http_method)(url)
    assert response.status_code == status
