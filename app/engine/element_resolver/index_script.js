(args) => {
    const [selector, includeHidden] = args;

    function isVisible(el) {
        const rect = el.getBoundingClientRect();

        if (rect.width === 0 && rect.height === 0) {
            return false;
        }

        const style = getComputedStyle(el);

        if (style.visibility === "hidden") {
            return false;
        }

        if (style.display === "none") {
            return false;
        }

        if (parseFloat(style.opacity) === 0) {
            return false;
        }

        return true;
    }

    function accessibleLabel(el) {
        const aria = el.getAttribute("aria-label");

        if (aria) {
            return aria.trim();
        }

        const labelledBy = el.getAttribute("aria-labelledby");

        if (labelledBy) {
            const joined = labelledBy
                .split(/\\s+/)
                .map((id) => {
                    const element = document.getElementById(id);

                    return element
                        ? (element.innerText || element.textContent)
                        : "";
                })
                .filter(Boolean)
                .join(" ");

            if (joined) {
                return joined.trim();
            }
        }

        if (el.labels && el.labels.length) {
            return Array
                .from(el.labels)
                .map((label) => label.innerText)
                .join(" ")
                .trim();
        }

        return "";
    }

    function ownText(el) {
        const raw =
            el.innerText !== undefined
                ? el.innerText
                : el.textContent;

        return (raw || "")
            .trim()
            .replace(/\\s+/g, " ")
            .slice(0, 200);
    }

    function contextText(el) {
        /*
         * Procura um contexto próximo do elemento.
         *
         * A ideia é evitar pegar o texto da página inteira.
         * Primeiro tentamos encontrar um container próximo
         * que represente um componente/card.
         */

        const preferredSelectors = [
            ".inventory_item",
            "[data-testid='inventory-item']",
            "[data-test='inventory-item']",
            "article",
            "[role='article']",
            "li"
        ];

        for (const selector of preferredSelectors) {
            const container = el.closest(selector);

            if (container) {
                return ownText(container);
            }
        }

        /*
         * Fallback genérico:
         * sobe alguns níveis na árvore procurando um
         * container com uma quantidade razoável de texto.
         */

        let parent = el.parentElement;

        for (let i = 0; i < 4 && parent; i++) {
            const text = ownText(parent);

            if (
                text &&
                text.length >= 10 &&
                text.length <= 500
            ) {
                return text;
            }

            parent = parent.parentElement;
        }

        return "";
    }

    const implicitRoles = {
        a: "link",
        button: "button",
        input: "input",
        select: "listbox",
        textarea: "textbox",
        summary: "button",
        label: "label"
    };

    const nodes = Array.from(
        document.querySelectorAll(selector)
    );

    const records = [];

    let index = 0;

    for (const el of nodes) {

        if (!includeHidden && !isVisible(el)) {
            continue;
        }

        const id = "el-" + index++;

        el.setAttribute("data-er-id", id);

        const tag = el.tagName.toLowerCase();

        const role =
            el.getAttribute("role")
            || implicitRoles[tag]
            || tag;

        const label = accessibleLabel(el);

        const text = ownText(el);

        const value =
            "value" in el
                ? String(el.value || "")
                : "";

        const placeholder =
            el.getAttribute("placeholder")
            || "";

        const title =
            el.getAttribute("title")
            || "";

        const testId =
            el.getAttribute("data-testid")
            || el.getAttribute("data-test")
            || el.getAttribute("data-qa")
            || "";

        const context = contextText(el);

        const rect = el.getBoundingClientRect();

        const content = [
            label,
            text,
            value,
            placeholder,
            title,
            testId,
            el.id,
            tag,
            role
        ]
        .filter(Boolean)
        .join(" ");

        records.push({
            id,
            tag,
            role,
            label,
            text,
            context: context.toLowerCase(),
            content: content.toLowerCase(),
            rect: {
                x: rect.x,
                y: rect.y,
                width: rect.width,
                height: rect.height
            }
        });
    }

    return records;
}