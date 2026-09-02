/** Open scratchpad links in a new tab without navigating the current page. */
export function wireOpenInNewTabLinks(root = document) {
    for (const link of root.querySelectorAll("a[data-open-tab]")) {
        link.addEventListener("click", (event) => {
            if (event.defaultPrevented)
                return;
            if (event.button !== 0)
                return;
            if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey)
                return;
            event.preventDefault();
            window.open(link.href, "_blank", "noopener,noreferrer");
        });
    }
}
