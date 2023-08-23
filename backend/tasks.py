from orders.celery import app

from .mailings import test_1, send_order_confirmation_email, send_reset_pass_email


@app.task
def test_task(task_id):
    res = test_1(task_id)
    return res


@app.task
def send_confirmation_email(order_id, to_user_list):
    send_order_confirmation_email(order_id, to_user_list)


@app.task
def send_reset_password_email(link, to_user_list):
    send_reset_pass_email(link, to_user_list)
