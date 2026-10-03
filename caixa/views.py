from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Sum
from django.core.paginator import Paginator
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from .forms import CaixaForm, MovimentacaoCaixaForm, SangriaForm, FechamentoCaixaForm
from .models import Caixa, MovimentacaoCaixa
from vendas.models import Venda

class OperacaoCaixaView(LoginRequiredMixin, TemplateView):

    template_name = 'caixa/operacao.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        caixa = (
            Caixa.objects
            .filter(
                status=Caixa.Status.ABERTO
            )
            .select_related('usuario_abertura')
            .order_by('-data_abertura')
            .first()
        )

        context['caixa'] = caixa

        if not caixa:
            context['vendas'] = Venda.objects.none()
            context['total_vendas'] = Decimal('0.00')
            context['total_entradas'] = Decimal('0.00')
            context['total_saidas'] = Decimal('0.00')
            context['saldo_atual'] = Decimal('0.00')
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

        total_vendas = (
            vendas.aggregate(
                total=Sum('total')
            )['total']
            or Decimal('0.00')
        )

        suprimentos = (
            MovimentacaoCaixa.objects
            .filter(
                caixa=caixa,
                tipo=MovimentacaoCaixa.Tipo.SUPRIMENTO
            )
            .select_related('usuario')
            .order_by('-data')
        )

        total_suprimentos = (
            suprimentos.aggregate(
                total=Sum('valor')
            )['total']
            or Decimal('0.00')
        )

        sangrias = (
            MovimentacaoCaixa.objects
            .filter(
                caixa=caixa,
                tipo=MovimentacaoCaixa.Tipo.SANGRIA
            )
            .select_related('usuario')
            .order_by('-data')
        )

        total_sangrias = (
            sangrias.aggregate(
                total=Sum('valor')
            )['total']
            or Decimal('0.00')
        )

        total_entradas = (
            total_vendas
            + total_suprimentos
        )

        total_saidas = total_sangrias

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
                'entrada': True,
            })

        for suprimento in suprimentos:
            movimentacoes.append({
                'data': suprimento.data,
                'descricao': suprimento.descricao,
                'tipo': 'SUPRIMENTO',
                'valor': suprimento.valor,
                'entrada': True,
            })

        for sangria in sangrias:
            movimentacoes.append({
                'data': sangria.data,
                'descricao': sangria.descricao,
                'tipo': 'SANGRIA',
                'valor': sangria.valor,
                'entrada': False,
            })

        movimentacoes.sort(
            key=lambda movimentacao: movimentacao['data'],
            reverse=True
        )

        paginator = Paginator(
            movimentacoes,
            15
        )

        pagina = self.request.GET.get('page')

        movimentacoes_paginadas = paginator.get_page(pagina)

        context['vendas'] = vendas
        context['total_vendas'] = total_vendas
        context['total_entradas'] = total_entradas
        context['total_saidas'] = total_saidas
        context['saldo_atual'] = saldo_atual
        context['movimentacoes'] = movimentacoes_paginadas
        context['page_obj'] = movimentacoes_paginadas

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

class SuprimentoCaixaView(LoginRequiredMixin, CreateView):

    model = MovimentacaoCaixa
    form_class = MovimentacaoCaixaForm
    template_name = 'caixa/suprimento.html'
    success_url = reverse_lazy('caixa:operacao')

    def get_caixa(self):
        return Caixa.objects.filter(
            status=Caixa.Status.ABERTO
        ).first()

    def dispatch(self, request, *args, **kwargs):

        if not self.get_caixa():
            return redirect('caixa:operacao')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        caixa = self.get_caixa()

        vendas = caixa.vendas.filter(
            status=Venda.Status.FINALIZADA
        ).aggregate(
            total=Sum('total')
        )['total'] or Decimal('0.00')

        suprimentos = caixa.movimentacoes.filter(
            tipo=MovimentacaoCaixa.Tipo.SUPRIMENTO
        ).aggregate(
            total=Sum('valor')
        )['total'] or Decimal('0.00')

        sangrias = caixa.movimentacoes.filter(
            tipo=MovimentacaoCaixa.Tipo.SANGRIA
        ).aggregate(
            total=Sum('valor')
        )['total'] or Decimal('0.00')

        saldo_atual = (
            caixa.valor_inicial
            + vendas
            + suprimentos
            - sangrias
        )

        context['caixa'] = caixa
        context['saldo_atual'] = saldo_atual
        context['responsavel'] = self.request.user

        return context

    def form_valid(self, form):

        form.instance.caixa = self.get_caixa()
        form.instance.usuario = self.request.user
        form.instance.tipo = MovimentacaoCaixa.Tipo.SUPRIMENTO

        return super().form_valid(form)

class SangriaCaixaView(LoginRequiredMixin, CreateView):

    model = MovimentacaoCaixa
    form_class = SangriaForm
    template_name = 'caixa/sangria.html'
    success_url = reverse_lazy('caixa:operacao')

    def dispatch(self, request, *args, **kwargs):

        self.caixa = Caixa.objects.filter(
            status=Caixa.Status.ABERTO
        ).first()

        if not self.caixa:
            return redirect('caixa:operacao')

        return super().dispatch(request, *args, **kwargs)

    def get_saldo_atual(self):

        total_vendas = (
            self.caixa.vendas
            .filter(
                status=Venda.Status.FINALIZADA
            )
            .aggregate(
                total=Sum('total')
            )['total']
            or Decimal('0.00')
        )

        total_suprimentos = (
            self.caixa.movimentacoes
            .filter(
                tipo=MovimentacaoCaixa.Tipo.SUPRIMENTO
            )
            .aggregate(
                total=Sum('valor')
            )['total']
            or Decimal('0.00')
        )

        total_sangrias = (
            self.caixa.movimentacoes
            .filter(
                tipo=MovimentacaoCaixa.Tipo.SANGRIA
            )
            .aggregate(
                total=Sum('valor')
            )['total']
            or Decimal('0.00')
        )

        saldo_atual = (
            self.caixa.valor_inicial
            + total_vendas
            + total_suprimentos
            - total_sangrias
        )

        return saldo_atual

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['caixa'] = self.caixa
        context['saldo_atual'] = self.get_saldo_atual()

        return context

    def form_valid(self, form):

        valor_sangria = form.cleaned_data['valor']
        saldo_atual = self.get_saldo_atual()

        if valor_sangria > saldo_atual:

            form.add_error(
                'valor',
                f'A sangria não pode ser maior que o saldo disponível de R$ {saldo_atual:.2f}.'
            )

            return self.form_invalid(form)

        form.instance.caixa = self.caixa
        form.instance.usuario = self.request.user
        form.instance.tipo = MovimentacaoCaixa.Tipo.SANGRIA

        return super().form_valid(form)
    
class FecharCaixaView(LoginRequiredMixin, UpdateView):

    model = Caixa
    form_class = FechamentoCaixaForm
    template_name = 'caixa/fechar.html'
    success_url = reverse_lazy('caixa:operacao')

    def get_object(self, queryset=None):

        return (
            Caixa.objects
            .filter(
                status=Caixa.Status.ABERTO
            )
            .order_by('-data_abertura')
            .first()
        )

    def dispatch(self, request, *args, **kwargs):

        if not self.get_object():

            messages.error(
                request,
                'Não existe nenhum caixa aberto.'
            )

            return redirect('caixa:operacao')

        return super().dispatch(
            request,
            *args,
            **kwargs
        )

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        caixa = self.object

        # ========================================
        # VENDAS
        # ========================================

        total_vendas = (
            caixa.vendas
            .filter(
                status=Venda.Status.FINALIZADA
            )
            .aggregate(
                total=Sum('total')
            )['total']
            or Decimal('0.00')
        )

        # ========================================
        # SUPRIMENTOS
        # ========================================

        total_suprimentos = (
            caixa.movimentacoes
            .filter(
                tipo=MovimentacaoCaixa.Tipo.SUPRIMENTO
            )
            .aggregate(
                total=Sum('valor')
            )['total']
            or Decimal('0.00')
        )

        # ========================================
        # SANGRIAS
        # ========================================

        total_sangrias = (
            caixa.movimentacoes
            .filter(
                tipo=MovimentacaoCaixa.Tipo.SANGRIA
            )
            .aggregate(
                total=Sum('valor')
            )['total']
            or Decimal('0.00')
        )

        # ========================================
        # SALDO ESPERADO
        # ========================================

        saldo_esperado = (
            caixa.valor_inicial
            + total_vendas
            + total_suprimentos
            - total_sangrias
        )

        context['caixa'] = caixa
        context['saldo_esperado'] = saldo_esperado

        return context

    def form_valid(self, form):

        caixa = form.instance

        caixa.usuario_fechamento = self.request.user
        caixa.data_fechamento = timezone.now()
        caixa.status = Caixa.Status.FECHADO

        response = super().form_valid(form)

        messages.success(
            self.request,
            'Caixa fechado com sucesso.'
        )

        return response