from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q

from .forms import ProdutoForm
from .models import Produto, Categoria

class ListaProdutos(ListView):
    model = Produto
    template_name = 'produtos/lista.html'
    context_object_name = 'produtos'
    paginate_by = 7

    def get_queryset(self):
        queryset = (
            Produto.objects
            .select_related('categoria')
            .order_by('nome')
        )

        busca = self.request.GET.get('busca', '').strip()
        categoria = self.request.GET.get('categoria', '').strip()

        if busca:
            queryset = queryset.filter(
                Q(nome__icontains=busca) |
                Q(codigo__icontains=busca)
            )

        if categoria:
            queryset = queryset.filter(
                categoria_id=categoria
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['categorias'] = Categoria.objects.order_by('nome')

        context['busca'] = self.request.GET.get(
            'busca',
            ''
        ).strip()

        context['categoria_id'] = self.request.GET.get(
            'categoria',
            ''
        ).strip()

        return context

class NovoProduto(CreateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'produtos/novo.html'
    success_url = reverse_lazy('produtos:lista')

class EditarProduto(UpdateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'produtos/editar.html'
    success_url = reverse_lazy('produtos:lista')

class ExcluirProduto(DeleteView):
    model = Produto
    template_name = 'produtos/excluir.html'
    success_url = reverse_lazy('produtos:lista')