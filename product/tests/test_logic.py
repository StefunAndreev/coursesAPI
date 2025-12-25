from http import HTTPStatus

from users.models import Balance, Subscription


def test_lesson_access_after_subscription(
        get_url,
        user_client,
        new_lessons,
        course,
        user
):
    """Тест проверяет, что уроки доступны после создания подписки."""
    url = get_url['lessons']
    response_without_sub = user_client.get(url)
    assert response_without_sub.status_code == HTTPStatus.FORBIDDEN, (
        'Уроки должны быть недоступны для пользователя без подписки.'
    )
    Subscription.objects.create(
        user=user,
        course=course,
    )
    response_with_sub = user_client.get(url)
    assert response_with_sub.status_code == HTTPStatus.OK, (
        'После создания подписки уроки должны стать доступны.'
    )


def test_anonymous_user_cant_create_subscription(client, get_url):
    """Анонимный пользователь не может купить подписку."""
    subscription_count = Subscription.objects.count()
    url = get_url['pay']
    response = client.post(url)
    assert response.status_code == HTTPStatus.UNAUTHORIZED, (
        'Анонимный пользователь не должен покупать подписку.'
    )
    assert Subscription.objects.count() == subscription_count, (
        'Количество подписок не должно увеличиваться после запроса от анонима.'
    )


def test_create_subscription(get_url, user_client, user, course):
    """Тест создания подписки."""
    url = get_url['pay']
    balance_before = user.user_bonuses.bonuses
    response = user_client.post(url)
    balance_after = Balance.objects.get(user=user).bonuses
    new_subscription = Subscription.objects.get()
    assert response.status_code == HTTPStatus.CREATED, (
        'Успешный запрос на покупку подписки должен возвращать статус CREATED.'
    )
    assert new_subscription.user == user, (
        'Созданная подписка должна быть привязана к правильному пользователю.'
    )
    assert new_subscription.course == course, (
        'Созданная подписка должна быть привязана к правильному курсу.'
    )
    assert balance_before - balance_after == course.price, (
        f'С баланса должно списаться ровно {course.price} единиц. '
        f'Было: {balance_before}, стало: {balance_after},'
        f'списано: {balance_before - balance_after}.'
    )


def test_unique_subscription(get_url, user_client):
    """Тест уникальности подписки."""
    Subscription.objects.all().delete()
    url = get_url['pay']
    response_1 = user_client.post(url)
    assert response_1.status_code == HTTPStatus.CREATED, (
        'Первая попытка покупки подписки должна быть успешной.'
    )
    subscription_count = Subscription.objects.count()
    response_2 = user_client.post(url)
    assert response_2.status_code == HTTPStatus.BAD_REQUEST, (
        'Повторная попытка покупки подписки на тот же курс должна вернуть.'
    )
    assert Subscription.objects.count() == subscription_count, (
        'Повторный запрос не должен создавать вторую подписку.'
    )


def test_insufficient_balance(get_url, user_client, user, course):
    """Тест создания подписки при недостаточном балансе."""
    subscription_count = Subscription.objects.count()
    url = get_url['pay']
    user.user_bonuses.bonuses = course.price - 1
    user.user_bonuses.save()
    balance_before = user.user_bonuses.bonuses
    response = user_client.post(url)
    balance_after = Balance.objects.get(user=user).bonuses
    assert response.status_code == HTTPStatus.BAD_REQUEST, (
        'Попытка покупки при недостаточном балансе должна вернуть BAD_REQUEST.'
    )
    assert Subscription.objects.count() == subscription_count, (
        'Подписка не должна быть создана при недостаточном балансе.'
    )
    assert balance_after == balance_before, (
        'Баланс не должен измениться при неудачной попытке покупки.'
    )
