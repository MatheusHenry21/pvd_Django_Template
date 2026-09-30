from django.db import models

class Categoria(models.Model):
    nome = models.CharField(
        max_length=100,
        unique=True
    )

    def __str__(self):
        return self.nome


class Produto(models.Model):
    codigo = models.CharField(
        max_length=50,
        unique=True
    )

    nome = models.CharField(
        max_length=150
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='produtos'
    )

    preco = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    estoque = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0
    )

    ativo = models.BooleanField(
        default=True
    )

    def __str__(self):
        return f'{self.codigo} - {self.nome}'