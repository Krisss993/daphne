from django.urls import path  
from . import views  
from django.conf import settings
from django.conf.urls.static import static
  
urlpatterns = [    
    path('upload/', views.file_upload_page, name='file_upload_page'),
    path('upload/<int:conversation_id>/', views.upload_file, name='upload_file'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
