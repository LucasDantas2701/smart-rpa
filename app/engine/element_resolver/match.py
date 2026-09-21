from dataclasses import dataclass, field

from playwright.sync_api import Locator, Page


@dataclass
class Match:
    id: str
    tag: str
    role: str
    label: str
    text: str
    content: str
    context: str
    rect: dict
    score: float
    page: Page = field(repr=False)

    @property
    def locator(self) -> Locator:
        return self.page.locator(
            f'[data-er-id="{self.id}"]'
        )

    def click(self, **kwargs) -> None:
        self.locator.click(**kwargs)

    def fill(self, value: str, **kwargs) -> None:
        self.locator.fill(value, **kwargs)

    def __repr__(self) -> str:
        return (
            f"Match("
            f"score={self.score:.2f}, "
            f"role='{self.role}', "
            f"text='{self.text}', "
            f"context='{self.context}'"
            f")"
        )