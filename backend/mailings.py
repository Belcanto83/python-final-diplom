import time

from django.conf import settings
from django.core.mail import send_mail


def test_1(task_id):
    print('Test task is started!')  # старт рассылки сообщений на внешнее API
    time.sleep(30)
    print('Test task is done!')
    return f'Task {task_id} is done!'


def send_order_confirmation_email(order_id, to_user_list: list, from_user=settings.EMAIL_HOST_USER):
    send_mail(
        f'Subject: order {order_id}',
        f'Your order {order_id} is confirmed!',
        from_user,
        to_user_list,
        fail_silently=False
    )


def send_reset_pass_email(link: str, to_user_list: list, from_user=settings.EMAIL_HOST_USER):
    send_mail(
        f'Subject: reset password',
        f'Please follow this link {link} to reset your password',
        from_user,
        to_user_list,
        fail_silently=False
    )


def send_email(subject: str, message: str, to_user_list: list, from_user=settings.EMAIL_HOST_USER):
    send_mail(
        subject,
        message,
        from_user,
        to_user_list,
        fail_silently=True
    )
