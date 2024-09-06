from django.urls import path  
from . import views  
from .views import conversation_list, index

app_name = 'langchain_stream'
  
urlpatterns = [  
    # path('', views.index, name='chat'),
    path('conversations/', conversation_list, name='conversation_list'),  # Show all conversations
    path('chat/<int:conversation_id>/', index, name='chat'),  # Load a specific conversation
    path('chat/', views.index, name='chat'),    # URL for creating a new chat
    path('chat/<int:conversation_id>/delete/', views.delete_conversation, name='delete_conversation'),  # Delete a conversation
    path('upload/<int:conversation_id>/', views.upload_file, name='upload_file'),
    path('download/<int:file_id>/', views.download_file, name='download_file'),
    path('file/<int:file_id>/delete/', views.delete_file, name='delete_file'),
    
]
