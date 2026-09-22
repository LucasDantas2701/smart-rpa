RESOLVER_ACTION_MAP = {
    "click": "click",
    "hover": "click",
    "check": "check",       # antes: "click" — agora aproveita os pesos dedicados (checkbox/switch/radio)
    "uncheck": "check",     # antes: "click" — uncheck usa o mesmo perfil de role que check
    "press": "click",
    "fill": "fill",
    "select": "select",     # antes: "fill" — agora aproveita os pesos dedicados (option/combobox/listbox)
    "extract_text": "extract",
    "extract_attribute": "extract",
    "extract_value": "extract",
}

DEFAULT_MIN_SCORE = 0.20
DEFAULT_AMBIGUITY_GAP = 0.08
DEFAULT_K = 5