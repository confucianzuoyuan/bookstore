# 进入python3的虚拟环境
# pip install fabric3

from fabric.api import *

env.user = 'root' # 阿里云一般都是root
env.hosts = ['www.zuoyuanandbaiyuan.com'] # 公网ip
env.password = 'xxxxxxxx' # 密码

def deploy():
  run('rm -rf bookstore/')
  run('rm -rf py2/ && rm -rf py3/')
  run('virtualenv -p python py2')
  run('pip install django==1.8.2 && django-admin startproject bookstore')
  with cd('bookstore'):
    run('python manage.py runserver 0.0.0.0:8000')
