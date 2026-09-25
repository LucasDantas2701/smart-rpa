"""O plano: uma lista de passos que o Executor sabe executar."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional

# Ações que o planejador pode usar e se exigem um valor.
ACTIONS = {
    "click": False,
    "hover": False,
    "check": False,
    "uncheck": False,
    "fill": True,          # valor = texto a digitar
    "select": True,        # valor = texto da opção
    "press": True,         # valor = tecla (ex.: "Enter")
    "extract_text": False,
}

# Esquema JSON exigido do modelo (formato "structured outputs" da OpenAI).
PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": list(ACTIONS)},
                    "description": {"type": "string"},
                    "value": {"type": ["string", "null"]},
                },
                "required": ["action", "description", "value"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["steps"],
    "additionalProperties": False,
}


class PlanError(ValueError):
    """O modelo devolveu algo que não é um plano válido."""


@dataclass
class Step:
    action: str
    description: str
    value: Optional[str] = None


@dataclass
class Plan:
    steps: list[Step]
    model: str = ""
    latency_s: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    attempts: int = 1
    raw: str = field(default="", repr=False)

    def to_dict(self) -> dict:
        return asdict(self)


def parse_plan(data: object) -> list[Step]:
    """Valida o JSON do modelo e devolve os passos. Lança PlanError com o motivo."""
    if not isinstance(data, dict) or not isinstance(data.get("steps"), list):
        raise PlanError('a resposta deve ser um objeto com a lista "steps"')

    steps = []
    for i, item in enumerate(data["steps"], 1):
        if not isinstance(item, dict):
            raise PlanError(f"passo {i} não é um objeto")
        action = item.get("action")
        description = (item.get("description") or "").strip()
        value = item.get("value")
        if action not in ACTIONS:
            raise PlanError(f'passo {i}: ação "{action}" não existe; use uma de {", ".join(ACTIONS)}')
        if not description:
            raise PlanError(f"passo {i}: descrição vazia")
        if ACTIONS[action] and (value is None or str(value).strip() == ""):
            raise PlanError(f'passo {i}: a ação "{action}" precisa de um valor')
        steps.append(Step(action, description, None if value is None else str(value)))
    return steps
