from fabric.api import *

env.user = 'root'
env.hosts = ['www.zuoyuanandbaiyuan.com']
env.password = 'xxxxxxxxxx'

def deploy():
  run('rm -rf bookstore/')
  run('rm -rf py2/ && rm -rf py3/')
  run('virtualenv -p python py2')
  run('pip install django==1.8.2 && django-admin startproject bookstore')
  with cd('bookstore'):
    run('python manage.py runserver 0.0.0.0:8000')
