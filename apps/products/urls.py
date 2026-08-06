from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='list'),
    path('adicionar/', views.ProductCreateView.as_view(), name='add'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.ProductUpdateView.as_view(), name='edit'),
    path('<int:pk>/excluir/', views.ProductDeleteView.as_view(), name='delete'),
]
