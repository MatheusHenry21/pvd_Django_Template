from django.db import models

from usuarios.models import Usuario
from caixa.models import Caixa
from produtos.models import Produto


class Venda(models.Model):

    class Status(models.TextChoices):
        ABERTA = 'ABERTA', 'Aberta'
        FINALIZADA = 'FINALIZADA', 'Finalizada'
        CANCELADA = 'CANCELADA', 'Cancelada'

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='vendas'
    )

    caixa = models.ForeignKey(
        Caixa,
        on_delete=models.PROTECT,
        related_name='vendas'
    )

    data = models.DateTimeField(
        auto_now_add=True
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ABERTA
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f'Venda #{self.id} - {self.get_status_display()}'


class ItemVenda(models.Model):

    venda = models.ForeignKey(
        Venda,
        on_delete=models.CASCADE,
        related_name='itens'
    )

    produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name='itens_venda'
    )

    quantidade = models.DecimalField(
        max_digits=10,
        decimal_places=3
    )

    preco_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return f'{self.produto.nome} - {self.quantidade}'