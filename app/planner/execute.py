"""Executa um plano com o ActionExecutor, passo a passo."""

from __future__ import annotations

from app.engine.action_executor import ActionExecutor, ActionResult

from .plan import Plan, Step


def run_step(executor: ActionExecutor, step: Step) -> ActionResult:
    a, d, v = step.action, step.description, step.value
    if a == "fill":
        return executor.fill(d, v)
    if a == "select":
        return executor.select(d, label=v)
    if a == "press":
        return executor.press(d, key=v)
    return getattr(executor, a)(d)  # click, hover, check, uncheck, extract_text


def run_plan(executor: ActionExecutor, plan: Plan, stop_on_failure: bool = True) -> list[tuple[Step, ActionResult]]:
    results = []
    for step in plan.steps:
        result = run_step(executor, step)
        results.append((step, result))
        if stop_on_failure and result.status != "success":
            break
    return results
