import string
import random

from django.http import JsonResponse
from django.shortcuts import redirect
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, GenericViewSet, ReadOnlyModelViewSet
from rest_framework.authtoken.models import Token

from .errors import IncorrectFileFormatError
from .filters import ProductInfoFilter
from .models import Shop, UserTypeChoices, User, ProductInfo, Order, OrderStatusChoices, Category, RestorePasswordToken
from .permissions import IsOwner
from .serializers import ShopSerializer, UserSerializer, ProductInfoSerializer, BasketSerializer, CategorySerializer, \
    GeneralShopSerializer
from .tasks import test_task, send_confirmation_email, send_reset_password_email


def index(request):
    return redirect('api/v1/')


class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  GenericViewSet):
    queryset = User.objects.order_by('username')
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ["retrieve", "update", "partial_update"]:
            return [IsAuthenticated()]
        return []

    @action(detail=True, methods=['POST'])
    def password_reset(self, request, pk=None):
        user = self.get_object()
        email = request.data.get('email')
        if user.email != email:
            return JsonResponse({'status': False, 'error': 'Please specify correct email'},
                                status=status.HTTP_403_FORBIDDEN)
        restore_pass_token = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(40))
        token_obj, created = RestorePasswordToken.objects.get_or_create(user=user,
                                                                        defaults={'user': user,
                                                                                  'token': restore_pass_token})
        restore_pass_link = f'http://127.0.0.1:8000/api/v1/users/password_reset/{token_obj.token}/'
        # print(restore_pass_link, type(restore_pass_link))
        # Отправляем пользователю email со спец. ссылкой (токеном) для восстановления пароля
        user_email = user.email
        send_reset_password_email.delay(restore_pass_link, [user_email])
        return JsonResponse({'status': True, 'message': 'Please check your mail'},
                            status=status.HTTP_201_CREATED)


class RestoreUserPassword(APIView):
    def get(self, request, *args, **kwargs):
        token = self.kwargs.get('token', None)
        token_obj = get_object_or_404(RestorePasswordToken, token=token)
        if token_obj:
            RestorePasswordToken.objects.get(user=token_obj.user).delete()
        token = get_object_or_404(Token, user=token_obj.user)
        # RestorePasswordToken.objects.get(user=token_obj.user).delete()
        return JsonResponse({'status': True, 'message': f'Your token: {token.key}'},
                            status=status.HTTP_200_OK)

# class ShopViewSet(ModelViewSet):
#     queryset = Shop.objects.order_by('name')
#     serializer_class = ShopSerializer
#     # filterset_fields = ['phone', 'mobile_operator_code']
#     # search_fields = ['tag', 'time_zone']
#     # ordering_fields = ['mobile_operator_code', 'tag', 'time_zone']


class CategoryViewSet(ReadOnlyModelViewSet):
    queryset = Category.objects.order_by('name')
    serializer_class = CategorySerializer
    filterset_fields = ['name']
    search_fields = ['name']
    ordering_fields = ['name']


class ProductViewSet(ReadOnlyModelViewSet):
    queryset = ProductInfo.objects.order_by('price_rrc')
    serializer_class = ProductInfoSerializer
    filterset_fields = ['article_nr']
    search_fields = ['name', 'article_nr']
    ordering_fields = ['price_rrc', 'name']
    filterset_class = ProductInfoFilter


class ShopView(APIView):
    def get(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            return self._detail(request, *args, **kwargs)
        return self._list(request, *args, **kwargs)

    def _detail(self, request, *args, **kwargs):
        shop = get_object_or_404(Shop, pk=kwargs['pk'])
        serializer = GeneralShopSerializer(instance=shop)
        return JsonResponse(serializer.data, charset='utf-8')

    def _list(self, request, *args, **kwargs):
        shops = Shop.objects.all().order_by('name')
        serializer = GeneralShopSerializer(shops, many=True)
        return JsonResponse(serializer.data, safe=False)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'status': False, 'error': 'Log in required'}, status=status.HTTP_403_FORBIDDEN)
        if request.user.type != UserTypeChoices.SHOP:
            return JsonResponse({'status': False, 'error': 'Only for shops'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ShopSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except IncorrectFileFormatError:
            return JsonResponse({'status': False, 'error': 'File has incorrect format'},
                                status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse(serializer.data)

    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'status': False, 'error': 'Log in required'}, status=status.HTTP_403_FORBIDDEN)
        if request.user.type != UserTypeChoices.SHOP:
            return JsonResponse({'status': False, 'error': 'Only for shops'}, status=status.HTTP_403_FORBIDDEN)
        try:
            instance = Shop.objects.get(pk=kwargs['pk'])
        except Shop.DoesNotExist:
            return JsonResponse({'status': False, 'error': 'Shop does not exist'}, status=status.HTTP_404_NOT_FOUND)
        if instance.user != request.user:
            return JsonResponse({'status': False, 'error': 'Only authorized user can update this shop'},
                                status=status.HTTP_403_FORBIDDEN)
        serializer = ShopSerializer(data=request.data, instance=instance, context={'request': request})
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except IncorrectFileFormatError:
            return JsonResponse({'status': False, 'error': 'File has incorrect format'},
                                status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse(serializer.data)


class BasketViewSet(ModelViewSet):
    queryset = Order.objects.all().order_by('-dt')
    serializer_class = BasketSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Order.objects.filter(user=user).order_by('-dt')
        return Order.objects.none()

    def update(self, request, *args, **kwargs):
        order = self.get_object()
        if order.status != OrderStatusChoices.BASKET:
            return JsonResponse({'status': False, 'error': 'It is not possible to update your order'},
                                status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['PATCH'])
    def confirm_order(self, request, pk=None):
        order = self.get_object()
        if order.status != OrderStatusChoices.BASKET:
            return JsonResponse({'status': False, 'error': 'It is not possible to update your order'},
                                status=status.HTTP_403_FORBIDDEN)
        order.status = OrderStatusChoices.CONFIRMED
        if not request.data.get('delivery_address'):
            return JsonResponse({'status': False, 'error': 'Please specify delivery address'},
                                status=status.HTTP_400_BAD_REQUEST)
        order.delivery_address = request.data['delivery_address']
        order.save()
        # Отправка email с подтверждением заказа
        # test_task.delay(1)
        user_email = order.user.email
        send_confirmation_email.delay(order.id, [user_email])
        return JsonResponse({'status': True, 'message': 'Your order is confirmed'},
                            status=status.HTTP_201_CREATED)
