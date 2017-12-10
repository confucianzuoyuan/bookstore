# 中间件示例，打印中间件执行语句
class BookMiddleware(object):
    def process_request(self, request):
        print("Middleware executed")

# 分别处理收到的请求和发出去的相应，要理解中间件的原理。
class AnotherMiddleware(object):
    def process_request(self, request):
        print("Another middleware executed")

    def process_response(self, request, response):
        print("AnotherMiddleware process_response executed")
        return response

# 记录用户访问的url地址
class UrlPathRecordMiddleware(object):
    '''记录用户访问的url地址'''
    EXCLUDE_URLS = ['/user/login/', '/user/logout/', '/user/register/']
    # 1./user/ 记录 url_path = /user/
    # 2./user/login/ url_path = /user/
    # 3./user/login_check/  url_path = /user/
    def process_view(self, request, view_func, *view_args, **view_kwargs):
        # 当用户请求的地址不在排除的列表中，同时不是ajax的get请求
        if request.path not in UrlPathRecordMiddleware.EXCLUDE_URLS and not request.is_ajax() and request.method == 'GET':
            request.session['url_path'] = request.path

BLOCKED_IPS = []
# 拦截在BLOCKED_IPS中的IP
class BlockedIpMiddleware(object):
    def process_request(self, request):
        if request.META['REMOTE_ADDR'] in BLOCKED_IPS:
            return http.HttpResponseForbidden('<h1>Forbidden</h1>')