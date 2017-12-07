from django.db import models
from db.base_model import BaseModel
from users.models import Passport
from books.models import Books
# Create your models here.
class Comments(BaseModel):
    disabled = models.BooleanField(default=False, verbose_name="禁用评论")
    user = models.ForeignKey('users.Passport', verbose_name="用户ID")
    book = models.ForeignKey('books.Books', verbose_name="书籍ID")
    content = models.CharField(max_length=1000, verbose_name="评论内容")

    class Meta:
        db_table = 's_comment_table'