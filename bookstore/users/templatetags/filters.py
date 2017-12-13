from django.template import Library

# 创建一个Library类的对象
register = Library()


# 创建一个过滤器函数
@register.filter
def order_status(status):
    '''返回订单状态对应的字符串'''
    status_dict =  {
        1:"待支付",
        2:"待发货",
        3:"待收货",
        4:"待评价",
        5:"已完成",
    }
    return status_dict[status]
