from datetime import datetime, timedelta

import pytest
from django.test.client import Client

from courses.models import Course, Lesson
from users.models import Subscription


@pytest.fixture
def admin(django_user_model):
    return django_user_model.objects.create(
        email='admin@gmail.com',
        username='admin',
        is_staff=True
    )


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create(
        email='user@gmail.com',
        username='user'
    )


@pytest.fixture
def admin_client(admin):
    client = Client()
    client.force_login(admin)
    return client


@pytest.fixture
def user_client(user):
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def course(admin):
    course = Course.objects.create(
        author=admin.username,
        title='Заголовок',
        start_date=datetime(2026, 1, 15, 10, 0),
        price=300,
    )
    return course


@pytest.fixture
def new_courses(admin):
    course_list = [
        Course(
            author=admin.username,
            title=f'Курс {index}',
            price=500,
            start_date=datetime.today() + timedelta(days=index)
        )
        for index in range(5)
    ]
    Course.objects.bulk_create(course_list)


@pytest.fixture
def lesson(course):
    lesson = Lesson.objects.create(
        course=course,
        title='Курс',
        link='https://example.com',
    )
    return lesson


@pytest.fixture
def new_lessons(course):
    lesson_list = [
        Lesson(
            course=course,
            title=f'Курс {index}',
            link=f'https://example.com/lesson/{index}',
        )
        for index in range(5)
    ]
    Lesson.objects.bulk_create(lesson_list)


@pytest.fixture
def get_url(course):
    return {
        'courses': '/api/v1/courses/',
        'lessons': f'/api/v1/courses/{course.id}/lessons/',
        'groups': f'/api/v1/courses/{course.id}/groups/',
        'pay': f'/api/v1/courses/{course.id}/pay/',
    }
