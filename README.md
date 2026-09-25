# Smart RPA

> Automação inteligente de processos web utilizando Playwright, agentes de IA e resolução adaptativa de elementos.

**Smart RPA** é um projeto experimental voltado para a construção de uma abordagem mais inteligente e flexível para **RPA (Robotic Process Automation)**.

A proposta é combinar automação de navegadores, resolução semântica de elementos e agentes de IA para criar automações capazes de **interpretar tarefas, executar ações e se adaptar a mudanças nas interfaces web**.

## Visão geral

Automações tradicionais de navegadores normalmente dependem de seletores definidos manualmente:

```python
page.locator('[data-test="add-to-cart"]').click()
```

Isso funciona enquanto a estrutura da página permanece estável. Pequenas alterações na interface podem fazer com que a automação deixe de funcionar.

O Smart RPA busca criar uma camada de abstração entre o agente e o navegador:

```text
Usuário
   │
   ▼
Agente de IA
   │
   ▼
Planejador / Orquestrador
   │
   ▼
Camada de Ações
   │
   ▼
Resolvedor de Elementos
   │
   ▼
Motor do Navegador
   │
   ▼
Playwright
   │
   ▼
Navegador
```

A ideia é que o agente descreva **o que precisa ser feito**, enquanto o sistema determina **como executar a ação**.

Por exemplo:

```text
"Adicione a mochila ao carrinho"
             │
             ▼
         Agente de IA
             │
             ▼
          ação: click
             │
             ▼
    Resolvedor de Elementos
             │
             ▼
Encontra o botão correspondente
             │
             ▼
          Playwright
```

## Status do projeto

🚧 **Em desenvolvimento / MVP**

Atualmente, o projeto possui a base para execução de automações web utilizando Playwright.

### Implementado

* [x] Integração com Playwright
* [x] Perfil persistente do navegador
* [x] Gerenciamento do ciclo de vida do navegador
* [x] Detecção de sessão/login
* [x] Ações de navegação
* [x] Interação com elementos
* [x] Extração de dados
* [x] Esperas e sincronização
* [x] Download de arquivos
* [x] Capturas de tela
* [x] Tratamento inicial de pop-ups
* [x] Estrutura modular de ações
* [x] Automação funcional utilizando o SauceDemo

### Próximo foco

O próximo estágio é implementar o **Resolvedor de Elementos**, permitindo que a automação encontre elementos de maneira semântica em vez de depender exclusivamente de seletores definidos manualmente.

## Arquitetura

```text
smart-rpa/
│
├── app/
│   ├── agent/
│   │   ├── agent.py
│   │   ├── planner.py
│   │   ├── executor.py
│   │   ├── memory.py
│   │   └── prompts/
│   │       └── system_prompt.txt
│   │
│   ├── browser/
│   │   ├── browser.py
│   │   ├── session.py
│   │   └── profile.py
│   │
│   ├── engine/
│   │   ├── browser_engine.py
│   │   ├── element_resolver.py
│   │   └── action_executor.py
│   │
│   ├── actions/
│   │   ├── navigation.py
│   │   ├── interaction.py
│   │   ├── extraction.py
│   │   ├── download.py
│   │   ├── wait.py
│   │   ├── screenshot.py
│   │   └── popups.py
│   │
│   ├── llm/
│   │   ├── client.py
│   │   ├── openai.py
│   │   ├── gemini.py
│   │   └── claude.py
│   │
│   ├── automation/
│   │   └── example_task.py
│   │
│   ├── config/
│   │   └── settings.py
│   │
│   └── main.py
│
├── profiles/
├── tests/
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## Tecnologias

* **Python**
* **Playwright**
* **RPA**
* **Automação de navegadores**
* **Agentes de IA**
* **LLMs**
* **Orquestração**
* **Resolução semântica de elementos**

## Automação do navegador

O Playwright é utilizado como o motor responsável pelo controle do navegador.

O projeto não pretende recriar um mecanismo de automação de navegadores do zero. O Playwright fornece a infraestrutura de baixo nível, enquanto o Smart RPA desenvolve as camadas de maior nível relacionadas à inteligência, resolução e orquestração.

Essa separação permite que o projeto se concentre em:

* Interpretação de intenções
* Planejamento de tarefas
* Resolução de elementos
* Execução de ações
* Recuperação de falhas
* Memória de execução
* Observabilidade
* Adaptação a mudanças na interface

## Sessões persistentes

O Smart RPA utiliza perfis persistentes do Playwright para manter sessões do navegador localmente.

Isso permite reutilizar uma sessão autenticada sem que credenciais precisem ser enviadas para o agente de IA.

O fluxo esperado é:

```text
Primeira execução
       │
       ▼
Abre o navegador
       │
       ▼
Usuário realiza o login
       │
       ▼
Sessão armazenada localmente
       │
       ▼
Próximas execuções
       │
       ▼
Reutilização da sessão
```

Os perfis do navegador são ignorados pelo Git e não fazem parte do repositório.

## Exemplo atual

Uma automação pode utilizar as ações disponíveis no projeto:

```python
navigate(
    page,
    "https://www.saucedemo.com/inventory.html"
)

click(
    page,
    '[data-test="add-to-cart-sauce-labs-backpack"]'
)

click(
    page,
    '[data-test="shopping-cart-link"]'
)

product_name = extract_text(
    page,
    ".inventory_item_name"
)
```

Atualmente, os seletores ainda são definidos manualmente.

O objetivo é evoluir para uma abordagem semântica, na qual a intenção possa ser descrita de maneira mais próxima da linguagem natural:

```python
click_element(
    page,
    "botão para adicionar a mochila ao carrinho"
)
```

O sistema então seria responsável por encontrar o elemento correspondente.

## Roadmap

### Fase 1 —
