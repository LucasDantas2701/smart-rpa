"""Lista curta dos elementos da página, para o planejador usar os nomes reais."""

from __future__ import annotations

from collections import Counter

from app.engine.disambiguation.describe import describe
from app.engine.element_resolver import ElementResolver


def page_elements(resolver: ElementResolver, limit: int = 80) -> list[str]:
    resolver.index("interactive")
    views = [describe(resolver.to_match(r), 0) for r in resolver.records]
    repeated = Counter((v.kind, v.name) for v in views)

    lines, seen = [], set()
    for record, v in zip(resolver.records, views):
        line = f'{v.kind} "{v.name}"'
        # Listas de opções levam as opções: o modelo precisa do texto exato.
        if record.get("options"):
            line += " [opções: " + " | ".join(record["options"][:10]) + "]"
        # Nomes repetidos (ex.: vários "Add to cart") levam o texto ao redor.
        if repeated[(v.kind, v.name)] > 1 and v.near:
            line += f" ({v.near[:40]})"
        if line not in seen:
            seen.add(line)
            lines.append(line)
        if len(lines) >= limit:
            break
    return lines
