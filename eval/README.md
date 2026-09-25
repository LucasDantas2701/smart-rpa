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

## Holdout (conjunto de teste fechado)

Os arquivos `cases/holdout_*.json` (split `test`) formam o conjunto fechado,
criado em 25/09/2026 **antes** das correções de verbo conflitante e da
recalibração dos limiares. Os casos do antigo split `test` viraram `dev`
(campo `split_original: "test"`), porque já tinham sido consultados.

Regras:

1. `python -m eval.run` nunca roda o holdout. Só `--final` roda, e o
   resultado sai com o sufixo `_FINAL` no nome do arquivo.
2. Rode `--final` **uma vez**, quando o desenvolvimento do Resolver estiver
   encerrado. Os números do artigo vêm dessa rodada.
3. Se algo for alterado depois de olhar o holdout, registre isso no artigo.
4. `--check` pode ser usado a qualquer momento: só confere se os seletores
   esperados existem, sem calcular scores.

### Consultas de colegas (recomendado)

As consultas do holdout foram escritas pelo mesmo autor das heurísticas
(viés de autoria). Para reduzir esse viés, peça a 2 ou 3 pessoas que:

1. abram cada página de `fixtures/holdout_*.html` no navegador;
2. escrevam, para 8 a 10 elementos, como pediriam aquela ação a um
   assistente ("quero cancelar o pedido do dia 3 de novembro");
3. sem ver o código nem os casos existentes.

Adicione essas consultas como novos casos `split: "test"`, com ids
`h-<pagina>-cNN`, e reporte os dois grupos separadamente no artigo.
