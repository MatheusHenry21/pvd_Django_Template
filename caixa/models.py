from django.db import models
from django.core.validators import MinValueValidator
from usuarios.models import Usuario


class Caixa(models.Model):

    class Status(models.TextChoices):
        ABERTO = 'ABERTO', 'Aberto'
        FECHADO = 'FECHADO', 'Fechado'

    usuario_abertura = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='caixas_abertos'
    )

    data_abertura = models.DateTimeField(auto_now_add=True)

    valor_inicial = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    usuario_fechamento = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='caixas_fechados',
        null=True,
        blank=True
    )

    data_fechamento = models.DateTimeField(
        null=True,
        blank=True
    )

    valor_final = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ABERTO
    )

    def __str__(self):
        return f'Caixa #{self.id} - {self.get_status_display()}'


class MovimentacaoCaixa(models.Model):

    class Tipo(models.TextChoices):
        SUPRIMENTO = 'SUPRIMENTO', 'Suprimento'
        SANGRIA = 'SANGRIA', 'Sangria'

    caixa = models.ForeignKey(
        Caixa,
        on_delete=models.CASCADE,
        related_name='movimentacoes'
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='movimentacoes_caixa'
    )

    tipo = models.CharField(
        max_length=12,
        choices=Tipo.choices
    )

    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    descricao = models.CharField(
        max_length=150
    )

    observacao = models.TextField(
        blank=True
    )

    data = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f'{self.get_tipo_display()} - R$ {self.valor}'