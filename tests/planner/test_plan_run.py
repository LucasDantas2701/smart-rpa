"""Testes da avaliação de tarefas completas (eval/plan_run.py), com LLM falso."""

import json

from app.planner import LLMPlanner
from eval.plan_run import INSTRUMENT, TASKS, run_task, summarize
from tests.planner.test_planner import FakeClient

TASK = next(t for t in json.loads(TASKS.read_text(encoding="utf-8"))["tasks"] if t["id"] == "p-usr-02")


def as_json(steps):
    return json.dumps({"steps": [dict(action=a, description=d, value=v) for a, d, v in steps]})


def fresh(page):
    page.set_default_timeout(3000)
    page.add_init_script(INSTRUMENT)
    return page


def test_plano_do_modelo_cumpre_a_tarefa(page):
    client = FakeClient(as_json(TASK["reference"]))
    r = run_task(fresh(page), LLMPlanner(client, "falso"), "falso", TASK, use_page=True)
    assert r.sucesso and r.plano_valido
    assert r.passos_ok == r.passos_plano == 2
    assert r.tokens_entrada == 100 and r.tokens_saida == 20
    assert "Selecionar Ana Souza" in client.calls[0]["messages"][1]["content"]  # recebeu a página


def test_plano_errado_nao_cumpre(page):
    client = FakeClient(as_json([["check", "caixa Selecionar Bruno Lima", None]]))
    r = run_task(fresh(page), LLMPlanner(client, "falso"), "falso", TASK, use_page=True)
    assert r.plano_valido and not r.sucesso
    assert r.verificacoes_ok < r.verificacoes


def test_modelo_sem_resposta_valida_e_registrado(page):
    client = FakeClient("não sei", "também não")
    r = run_task(fresh(page), LLMPlanner(client, "falso"), "falso", TASK, use_page=True)
    assert not r.plano_valido and not r.sucesso
    assert "PlanError" in r.erro
    s = summarize([r])
    assert s["plano_valido"] == 0 and s["sucesso"] == 0
