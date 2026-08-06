from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    path('categorias/', views.ServiceCategoryListView.as_view(), name='category_list'),
    path('categorias/adicionar/', views.ServiceCategoryCreateView.as_view(), name='category_create'),
    path('categorias/<int:pk>/editar/', views.ServiceCategoryUpdateView.as_view(), name='category_edit'),
    path('categorias/<int:pk>/excluir/', views.ServiceCategoryDeleteView.as_view(), name='category_delete'),
    path('', views.ServiceListView.as_view(), name='list'),
    path('adicionar/', views.ServiceCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ServiceDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.ServiceUpdateView.as_view(), name='edit'),
    path('<int:pk>/excluir/', views.ServiceDeleteView.as_view(), name='delete'),
]
