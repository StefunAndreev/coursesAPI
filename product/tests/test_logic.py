from http import HTTPStatus

from users.models import Balance, Subscription


def test_lesson_access_after_subscription(
        get_url,
        user_client,
        new_lessons,
        course,
        user
):
    """Тест проверяет, что уроки доступены после создания подписки."""
    url = get_url['lessons']
    response_without_sub = user_client.get(url)
    assert response_without_sub.status_code == HTTPStatus.FORBIDDEN
    Subscription.objects.create(
        user=user,
        course=course,
    )
    response_with_sub = user_client.get(url)
    assert response_with_sub.status_code == HTTPStatus.OK


def test_anonymous_user_cant_create_subscription(client, get_url):
    """Анонимный пользователь не может купить подписку."""
    subscription_count = Subscription.objects.count()
    url = get_url['pay']
    response = client.post(url)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert Subscription.objects.count() == subscription_count


def test_create_subscription(get_url, user_client, user, course):
    """Тест создания подписки."""
    url = get_url['pay']
    balance_before = user.user_bonuses.bonuses
    response = user_client.post(url)
    balance_after = Balance.objects.get(user=user).bonuses
    new_subscription = Subscription.objects.get()
    assert response.status_code == HTTPStatus.CREATED
    assert new_subscription.user == user
    assert new_subscription.course == course
    assert balance_before - balance_after == course.price


def test_unique_subscription(get_url, user_client):
    """Тест уникальности подписки."""
    Subscription.objects.all().delete()
    url = get_url['pay']
    response_1 = user_client.post(url)
    assert response_1.status_code == HTTPStatus.CREATED
    subscription_count = Subscription.objects.count()
    response_2 = user_client.post(url)
    assert response_2.status_code == HTTPStatus.BAD_REQUEST
    assert Subscription.objects.count() == subscription_count


def test_insufficient_balance(get_url, user_client, user, course):
    """Тест создания подписки при недостаточном балансе."""
    subscription_count = Subscription.objects.count()
    url = get_url['pay']
    user.user_bonuses.bonuses = course.price - 1
    user.user_bonuses.save()
    balance_before = user.user_bonuses.bonuses
    response = user_client.post(url)
    balance_after = Balance.objects.get(user=user).bonuses
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert Subscription.objects.count() == subscription_count
    assert balance_after == balance_before
