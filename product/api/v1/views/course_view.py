from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from api.v1.permissions import IsStudentOrIsAdmin, ReadOnlyOrIsAdmin
from api.v1.serializers.course_serializer import (CourseSerializer,
                                                  CreateCourseSerializer,
                                                  CreateGroupSerializer,
                                                  CreateLessonSerializer,
                                                  GroupSerializer,
                                                  LessonSerializer)
from api.v1.serializers.user_serializer import SubscriptionSerializer
from courses.models import Course
from users.models import Balance, Subscription


class LessonViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с уроками."""

    permission_classes = (IsStudentOrIsAdmin,)

    def get_serializer_class(self):
        """Функция для выбора сериализатора."""
        if self.action in ['list', 'retrieve']:
            return LessonSerializer
        return CreateLessonSerializer

    def get_course(self):
        """Получает курс по ID."""
        return get_object_or_404(Course, id=self.kwargs.get('course_id'))

    def perform_create(self, serializer):
        """Создает новый урок."""
        serializer.save(course=self.get_course())

    def get_queryset(self):
        """Возвращает уроки, только если у пользователя есть подписка."""
        course = self.get_course()
        if not (self.request.user.is_staff or Subscription.objects.filter(
            user=self.request.user,
            course=course,
        ).exists()):
            raise PermissionDenied('У вас нет активной подписки на этот курс.')
        return course.lessons.all()


class GroupViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с группами."""

    permission_classes = (permissions.IsAdminUser,)

    def get_serializer_class(self):
        """Функция для выбора сериализатора."""
        if self.action in ['list', 'retrieve']:
            return GroupSerializer
        return CreateGroupSerializer

    def get_course(self):
        """Получает курс по ID."""
        return get_object_or_404(Course, id=self.kwargs.get('course_id'))

    def perform_create(self, serializer):
        """Создает новую группу."""
        serializer.save(course=self.get_course())

    def get_queryset(self):
        """Получает список всех групп."""
        return self.get_course().groups.all()


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с курсами."""

    queryset = Course.objects.all()
    permission_classes = (ReadOnlyOrIsAdmin,)

    def get_serializer_class(self):
        """Функция для выбора сериализатора."""
        if self.action in ['list', 'retrieve']:
            return CourseSerializer
        elif self.action == 'pay':
            return SubscriptionSerializer
        return CreateCourseSerializer

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[IsStudentOrIsAdmin]
    )
    def pay(self, request, pk):
        """Покупка доступа к курсу (подписка на курс)."""
        try:
            course = self.get_object()
        except Course.DoesNotExist:
            return Response(
                {'error': 'Курс не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
        user = request.user
        balance = Balance.objects.get(user=user)
        if balance.bonuses < course.price:
            return Response(
                {
                    'error': 'Недостаточно бонусов',
                    'current_balance': balance.bonuses,
                    'required': course.price,
                    'deficit': course.price - balance.bonuses
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription_serializer = SubscriptionSerializer(
            data={'course': course.id},
            context={'request': request}
        )
        if not subscription_serializer.is_valid():
            return Response(
                subscription_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        with transaction.atomic():
            previous_balance = balance.bonuses
            balance.bonuses -= course.price
            balance.save()
            subscription = subscription_serializer.save()
        response_serializer = SubscriptionSerializer(subscription)
        data = {
            'message': 'Курс успешно оплачен',
            'subscription': response_serializer.data,
            'payment_details': {
                'amount': course.price,
                'previous_balance': previous_balance,
                'remaining_balance': balance.bonuses
            }
        }
        return Response(data, status=status.HTTP_201_CREATED)
