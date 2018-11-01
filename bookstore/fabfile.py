# 进入python3的虚拟环境
# pip install fabric3
# 运行程序为'fab 函数名'
# fab deploy

from fabric.api import *

env.user = 'root' # 阿里云一般都是root
env.hosts = ['www.zuoyuanandbaiyuan.com'] # 公网ip
env.password = 'xxxxxxxx' # 密码

def hello():
  local('echo hello')

def deploy():
  run('rm -rf bookstore/')
  run('pip install django==1.8.2 && django-admin startproject bookstore')
  with cd('bookstore'):
    try:
      run('python manage.py runserver 0.0.0.0:8000')
    except:
      run('python3 manage.py runserver 0.0.0.0:8000')
