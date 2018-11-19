from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

@shared_task
def send_active_email(token, username, email):
    '''发送激活邮件'''
    subject = '尚硅谷书城用户激活' # 标题
    message = ''
    sender = settings.EMAIL_FROM # 发件人
    receiver = [email] # 收件人列表
    html_message = '<a href="http://127.0.0.1:8000/user/active/%s/">http://127.0.0.1:8000/user/active/</a>'%token
    send_mail(subject, message, sender, receiver, html_message=html_message)
