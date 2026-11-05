
from decimal import Decimal

from django.contrib.auth.views import LoginView
from django.db.models import Sum
from django.utils import timezone

from produtos.models import Produto
from vendas.models import Venda
from clientes.models import Cliente


class LoginPVDView(LoginView):
    template_name = 'usuarios/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = timezone.localdate()

        vendas_hoje = Venda.objects.filter(
            data__date=hoje,
            status='FINALIZADA',
        ).aggregate(total=Sum('total'))['total']

        context['vendas_hoje'] = vendas_hoje or Decimal('0.00')
        context['produtos_ativos'] = Produto.objects.filter(ativo=True).count()
        context['total_clientes'] = Cliente.objects.count()

        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        form.fields['username'].widget.attrs.update({
            'placeholder': 'Digite seu usuário',
            'autocomplete': 'username',
        })

        form.fields['password'].widget.attrs.update({
            'placeholder': 'Digite sua senha',
            'autocomplete': 'current-password',
        })

        return form