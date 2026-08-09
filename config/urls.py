from django.contrib import admin
from django.urls import path, include, re_path
from django.http import  HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from .views import home
from django.contrib.auth import views as auth_views

def favicon(request):
    return HttpResponse(status=204)

# URL Patterns
urlpatterns = [
    path("", home),  
    re_path(r'^favicon.ico$', favicon), 
    path('admin/', admin.site.urls), 
    
    path('summernote/', include('django_summernote.urls')),
    path('api/v1/', include([
        path('schema-viewer/', include('schema_viewer.urls')),
        path('auth/', include('apps.auths.urls')),
        path('file/', include('apps.file_uploader.urls')),
        path('notification/', include('apps.notification.urls')),
        path('employees/', include('apps.employee.urls')),
        path('productions/', include('apps.production.urls')),
        path('customers/', include('apps.customer.urls')),
        path('collection/', include('apps.collection.urls')),
        path('shop/', include('apps.shop.urls')),
        path('cart/', include('apps.cart.urls')),
        path('order/', include('apps.order.urls')),
        path('delivery/manage/', include('apps.delivery_manage.urls')),
        path('equipments/', include('apps.equipment.urls')),
    ])),
]

# Static files for development mode
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
