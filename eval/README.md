# Avaliação do Resolver (Peça 10)

Rodar, na raiz do projeto:

    python -m eval.run --offline -v     # só as páginas locais, mostrando cada caso
    python -m eval.run                  # inclui sites reais (SauceDemo)
    python -m eval.run --split test     # só o conjunto de teste
    python -m eval.run --sweep          # testa combinações de score mínimo × gap

Cada execução grava `results/<data>_<commit>.csv` (um caso por linha) e um `.json` com o resumo.

## Formato de um arquivo de casos (`cases/<site>.json`)

    {
      "site": "loja",
      "fixture": "loja.html",           // página local em fixtures/  (ou "url": "https://...")
      "setup": "saucedemo_login",       // opcional: função em setups.py
      "requires_network": false,
      "cases": [
        {"id": "loja-01", "split": "dev", "action": "click",
         "query": "adicionar os fones de ouvido ao carrinho",
         "expected": ".card:nth-of-type(2) .add"}
      ]
    }

- `action`: nome da ação do Executor (click, fill, check, select, extract_text...).
- `expected`: seletor CSS (ou do Playwright, como `:has-text()`) do elemento certo.
  Se mais de um elemento for aceitável, o seletor pode casar com vários.
- `split`: `dev` para ajustar pesos e sinônimos; `test` só para medir.
- `synonyms` (opcional, no nível do site): vocabulário específico, passado ao Resolver.

## Regra de ouro

Ajuste pesos, sinônimos e heurísticas olhando **apenas** o `dev`.
O número que vai para o artigo é o do `test`. Se você melhorar o código
olhando os casos de teste, o resultado deixa de medir generalização.

## Resultados por caso (`outcome`)

| valor | significado |
|---|---|
| `acerto` | o Executor decidiu e escolheu o elemento certo |
| `erro_silencioso` | o Executor decidiu, mas escolheu o elemento **errado** (o pior caso) |
| `recusa_evitavel` | o certo estava em 1º, mas o Executor recusou (limiar conservador) |
| `recusa_correta` | o Executor recusou e o 1º estava errado (evitou um erro) |
| `falha_percepcao` | o elemento certo nem foi indexado pelo `index_script.js` |
