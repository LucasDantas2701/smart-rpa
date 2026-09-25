"""
Perfis de modelo (arquivo llm_profiles.json na raiz do projeto).

Cada perfil diz ONDE está o modelo e COMO autenticar, sem guardar a
chave: "api_key_env" é o NOME da variável de ambiente com a chave.
Todos usam o formato da API da OpenAI, que o Ollama também aceita.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from openai import OpenAI

DEFAULT_FILE = Path(__file__).resolve().parents[2] / "llm_profiles.json"


class ConfigError(RuntimeError):
    pass


@dataclass
class LLMProfile:
    name: str
    model: str
    base_url: Optional[str] = None       # None = API da OpenAI
    api_key_env: Optional[str] = None    # None = sem chave (ex.: Ollama local)
    temperature: float = 0.0
    timeout_s: float = 180.0
    extra_body: Optional[dict] = None    # parâmetros extras do servidor (ex.: desligar o raciocínio)

    def planner(self):
        """Planejador pronto para este perfil."""
        from .planner import LLMPlanner
        return LLMPlanner(self.client(), self.model, temperature=self.temperature, extra_body=self.extra_body)

    def api_key(self) -> str:
        if not self.api_key_env:
            return "sem-chave"  # o Ollama ignora a chave, mas o SDK exige uma
        key = os.environ.get(self.api_key_env)
        if not key:
            raise ConfigError(
                f'O perfil "{self.name}" precisa da variável de ambiente {self.api_key_env}.\n'
                f'No Windows: setx {self.api_key_env} "sua-chave" (e abra um terminal novo).'
            )
        return key

    def client(self) -> OpenAI:
        if not self.model or self.model.startswith("COLOQUE"):
            raise ConfigError(f'Defina o campo "model" do perfil "{self.name}" em llm_profiles.json.')
        return OpenAI(api_key=self.api_key(), base_url=self.base_url, timeout=self.timeout_s)


def load_profiles(path: Path | str = DEFAULT_FILE) -> dict[str, LLMProfile]:
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"Arquivo de perfis não encontrado: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return {p["name"]: LLMProfile(**p) for p in data["profiles"]}


def get_profile(name: str, path: Path | str = DEFAULT_FILE) -> LLMProfile:
    profiles = load_profiles(path)
    if name not in profiles:
        raise ConfigError(f'Perfil "{name}" não existe. Disponíveis: {", ".join(profiles)}')
    return profiles[name]
