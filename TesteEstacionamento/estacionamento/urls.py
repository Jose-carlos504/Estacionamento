from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path(
        'configurar/',
        views.configurar_vagas,
        name='configurar_vagas'
    ),

     path(
        'entrada/',
        views.entrada_veiculo,
        name='entrada_veiculo'
    ),
    path(
    'saida/',
    views.saida_veiculo,
    name='saida_veiculo'
    ),
    
    # Authentication and Panel URLs
    path('login/', views.login_view, name='login'),
    path('painel/', views.painel, name='painel'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path('usuarios/', views.gerenciar_usuarios, name='gerenciar_usuarios'),
    path('estacionamento/<int:estacionamento_id>/editar/', views.editar_estacionamento, name='editar_estacionamento'),
    
    # Authentication URLs
    path('logout/', views.logout_view, name='logout'),
    path('vendas/', RedirectView.as_view(pattern_name='home', permanent=False)),
]
