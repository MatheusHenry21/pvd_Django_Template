from django.urls import path

from . import views

app_name = 'produtos'

urlpatterns = [
    path('', views.ListaProdutos.as_view(), name='lista'),
    path('novo/', views.NovoProduto.as_view(), name='novo'),
    path('editar/<int:pk>/', views.EditarProduto.as_view(), name='editar'),
    path('excluir/<int:pk>', views.ExcluirProduto.as_view(), name='excluir')
]