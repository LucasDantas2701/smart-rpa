import re


DEFAULT_SELECTOR = ",".join([
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "a[href]",
    "button",
    "input",
    "select",
    "textarea",
    "[role]",
    "[contenteditable]",
    "[tabindex]",
    "[data-testid]",
    "[data-test]",
    "[data-qa]",
    "summary",
    "label",
])


TOKEN_RE = re.compile(
    r"[^a-z0-9à-ÿ]+"
)


SYNONYMS = {
    "botão": "button",
    "botoes": "button",
    "botões": "button",

    "adicionar": "add",
    "adicione": "add",

    "carrinho": "cart",
    "mochila": "backpack",
    "bicicleta": "bike",
    "luz": "light",
    "camisa": "shirt",
    "jaqueta": "jacket",
    "macacão": "onesie",

    "comprar": "buy",

    "remover": "remove",
    "excluir": "delete",
    "apagar": "delete",

    "selecionar": "select",
    "escolher": "choose",

    "buscar": "search",
    "pesquisar": "search",

    "continuar": "continue",
    "voltar": "back",

    "enviar": "send",
    "confirmar": "confirm",
    "cancelar": "cancel",
    "salvar": "save",
    "atualizar": "update",

    "filtrar": "filter",
    "ordenar": "sort",

    "abrir": "open",
    "fechar": "close",

    "entrar": "login",
    "sair": "logout",
}


ACTION_WORDS = {
    "add",
    "remove",
    "delete",
    "buy",
    "purchase",
    "submit",
    "save",
    "cancel",
    "confirm",
    "open",
    "close",
    "select",
    "choose",
    "click",
    "edit",
    "update",
    "search",
    "login",
    "logout",
    "signup",
    "subscribe",
    "upload",
    "download",
    "send",
    "apply",
    "filter",
    "sort",
    "checkout",
    "increase",
    "decrease",
    "view",
    "continue",
    "next",
    "back",
    "clear",
}


STOPWORDS = {
    "a",
    "o",
    "as",
    "os",
    "um",
    "uma",
    "uns",
    "umas",
    "de",
    "do",
    "da",
    "dos",
    "das",
    "em",
    "no",
    "na",
    "nos",
    "nas",
    "para",
    "por",
    "com",
    "sem",
    "ao",
    "aos",
    "à",
    "às",
}


STRUCTURAL_WORDS = {
    "button",
    "link",
    "input",
    "textbox",
    "field",
    "element",
    "elemento",
}


ACTION_CONTENT_BONUS = 0.30
ACTION_MISMATCH_DAMPING = 0.55

OBJECT_CONTEXT_BONUS = 0.30
OBJECT_MISMATCH_DAMPING = 0.70

EXTRACT_TEXT_BONUS = 0.15


ACTION_ROLE_WEIGHTS = {
    "click": {
        "button": 0.15,
        "link": 0.12,
        "checkbox": 0.10,
        "radio": 0.10,
        "combobox": 0.08,
        "div": -0.05,
        "span": -0.05,
        "p": -0.05,
    },
    "fill": {
        "textbox": 0.15,
        "input": 0.15,
        "textarea": 0.15,
        "combobox": 0.10,
        "button": -0.10,
        "link": -0.10,
    },
    "extract": {
        "button": 0.0,
        "link": 0.0,
    },
}