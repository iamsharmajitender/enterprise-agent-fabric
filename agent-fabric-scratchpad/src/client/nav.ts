/** Open scratchpad links in a new tab without navigating the current page. */
export function wireOpenInNewTabLinks(root: ParentNode = document): void {
  for (const link of Array.from(root.querySelectorAll<HTMLAnchorElement>("a[data-open-tab]"))) {
    link.addEventListener("click", (event: MouseEvent) => {
      if (event.defaultPrevented) return;
      if (event.button !== 0) return;
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      window.open(link.href, "_blank", "noopener,noreferrer");
    });
  }
}
