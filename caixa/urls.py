from django.urls import path
from . import views

app_name = 'caixa'

urlpatterns = [
    path('', views.OperacaoCaixaView.as_view(), name='operacao'),
    path('abrir/', views.AbrirCaixa.as_view(), name='abrir'),
    path('historico/', views.HistoricoCaixa.as_view(), name='historico'), 
    path('suprimento/', views.SuprimentoCaixaView.as_view(), name='suprimento'),
    path('sangria/', views.SangriaCaixaView.as_view(), name='sangria'),
]