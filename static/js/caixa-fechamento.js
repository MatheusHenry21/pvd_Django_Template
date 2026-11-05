const faixa = document.getElementById("caixa-diferenca");
const resultado = document.getElementById("caixa-diferenca-valor");
const saldoElemento = document.getElementById("caixa-saldo-esperado");

if (faixa && resultado && saldoElemento) {
    const campo = document.getElementById(faixa.dataset.campoId);

    // Converte valores com até duas casas decimais para centavos.
    function paraCentavos(valor) {
        const texto = String(valor).trim().replace(",", ".");

        if (!/^\d+(?:\.\d{1,2})?$/.test(texto)) {
            return null;
        }

        const [inteiros, decimais = ""] = texto.split(".");

        const centavos =
            Number(inteiros) * 100 +
            Number(decimais.padEnd(2, "0"));

        return Number.isSafeInteger(centavos) ? centavos : null;
    }

    const saldoEsperado = paraCentavos(
        JSON.parse(saldoElemento.textContent)
    );

    const moeda = new Intl.NumberFormat("pt-BR", {
        style: "currency",
        currency: "BRL"
    });

    function atualizarDiferenca() {
        const valorContado = paraCentavos(campo.value);

        faixa.classList.remove(
            "caixa-diferenca-negativa",
            "caixa-diferenca-zero",
            "caixa-diferenca-positiva"
        );

        if (
            valorContado === null ||
            saldoEsperado === null ||
            !campo.validity.valid
        ) {
            faixa.hidden = true;
            resultado.textContent = "";
            return;
        }

        const diferenca = valorContado - saldoEsperado;

        let classe = "caixa-diferenca-zero";
        let sinal = "";

        if (diferenca < 0) {
            classe = "caixa-diferenca-negativa";
            sinal = "− ";
        } else if (diferenca > 0) {
            classe = "caixa-diferenca-positiva";
            sinal = "+ ";
        }

        faixa.classList.add(classe);

        resultado.textContent =
            sinal + moeda.format(Math.abs(diferenca) / 100);

        faixa.hidden = false;
    }

    if (campo) {
        campo.addEventListener("input", atualizarDiferenca);
        atualizarDiferenca();
    }
}