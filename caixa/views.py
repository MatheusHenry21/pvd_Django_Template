from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, TemplateView

from .forms import CaixaForm
from .models import Caixa
from vendas.models import Venda

class OperacaoCaixaView(TemplateView):
    template_name = 'caixa/operacao.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        caixa = (
            Caixa.objects
            .filter(status=Caixa.Status.ABERTO)
            .select_related('usuario_abertura')
            .order_by('-data_abertura')
            .first()
        )

        context['caixa'] = caixa

        if not caixa:
            context['vendas'] = Venda.objects.none()
            context['total_vendas'] = 0
            context['total_entradas'] = 0
            context['total_saidas'] = 0
            context['saldo_atual'] = 0
            context['movimentacoes'] = []

            return context

        vendas = (
            Venda.objects
            .filter(
                caixa=caixa,
                status=Venda.Status.FINALIZADA
            )
            .select_related('usuario')
            .order_by('-data')
        )

        total_vendas = sum(
            venda.total for venda in vendas
        )

        total_entradas = total_vendas
        total_saidas = 0
        saldo_atual = (
            caixa.valor_inicial
            + total_entradas
            - total_saidas
        )

        movimentacoes = []

        for venda in vendas:
            movimentacoes.append({
                'data': venda.data,
                'descricao': f'Venda #{venda.id:05d}',
                'tipo': 'VENDA',
                'valor': venda.total,
            })

        context['vendas'] = vendas
        context['total_vendas'] = total_vendas
        context['total_entradas'] = total_entradas
        context['total_saidas'] = total_saidas
        context['saldo_atual'] = saldo_atual
        context['movimentacoes'] = movimentacoes

        return context

class AbrirCaixa(LoginRequiredMixin, CreateView):

    model = Caixa
    form_class = CaixaForm

    template_name = 'caixa/abrir.html'

    success_url = reverse_lazy('caixa:operacao')

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['responsavel'] = self.request.user
        context['data_hora'] = timezone.localtime()

        return context

    def dispatch(self, request, *args, **kwargs):

        if Caixa.objects.filter(
            status=Caixa.Status.ABERTO
        ).exists():

            messages.error(
                request,
                'Já existe um caixa aberto.'
            )

            return redirect('caixa:operacao')

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):

        form.instance.usuario_abertura = self.request.user

        form.instance.status = Caixa.Status.ABERTO

        response = super().form_valid(form)

        messages.success(
            self.request,
            'Caixa aberto com sucesso.'
        )

        return response


class HistoricoCaixa(LoginRequiredMixin, ListView):

    model = Caixa

    template_name = 'caixa/historico.html'

    context_object_name = 'caixas'

    def get_queryset(self):

        return (
            Caixa.objects
            .select_related(
                'usuario_abertura',
                'usuario_fechamento'
            )
            .order_by('-data_abertura')
        )