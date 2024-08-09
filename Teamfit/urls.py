"""
URL configuration for Teamfit project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, reverse_lazy
# from django.views.generic.base import RedirectView
# from django_plotly_dash.views import add_to_session

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    # path("django_plotly_dash/add_to_session/", add_to_session),
    # path("django_plotly_dash/", include("django_plotly_dash.urls")),
    #path('api/', include('apirest.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
