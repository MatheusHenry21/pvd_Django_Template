from django.urls import path
from . import views

app_name = 'caixa'

urlpatterns = [
    path('', views.OperacaoCaixaView.as_view(), name='operacao'),
    path('abrir/', views.AbrirCaixa.as_view(), name='abrir'),
    path('historico/', views.HistoricoCaixa.as_view(), name='historico'),
]