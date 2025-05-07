// remove nav/toc for page that has enough width
document$.subscribe(function() {
  const sidebar = document.querySelector("div.md-sidebar.md-sidebar--primary");
  if (!document.querySelector('.jp-Notebook') || !sidebar) return;

  // create an observer to monitor the change of `style` attribute
  const observer = new MutationObserver((mutations) => {
    mutations.forEach(mutation => {
      if (mutation.attributeName === 'style') {
        const hasTop = sidebar.style.top && sidebar.style.top !== '';
        if (hasTop) {
          sidebar.remove();
          observer.disconnect();
        }
      }
    });
  });

  // spy `style` attribute
  observer.observe(sidebar, { attributes: true });
});

// toc collapse functionality
function initTOCCollapse() {
  const tocNavs = document.querySelectorAll(".md-nav--secondary .md-nav__item > .md-nav__link");

  tocNavs.forEach(link => {
    if (link.dataset.tocInit) return;
    link.dataset.tocInit = "true";

    const parentItem = link.parentElement;
    const submenu = parentItem.querySelector(".md-nav");

    if (submenu) {
      parentItem.classList.add("has-submenu");

      // create a guide line
      const guideLine = document.createElement("div");
      guideLine.className = "toc-guide-line";
      parentItem.appendChild(guideLine);

      // Ensure the parent container supports absolute positioning.
      parentItem.style.position = "relative"; 

      // Create a collapse button
      const toggleBtn = document.createElement("span");
      toggleBtn.className = "toc-toggle-icon";
      toggleBtn.textContent = "⊕";
      toggleBtn.setAttribute("aria-label", "Toggle submenu");

      // Insert the icon before the linked content
      link.insertBefore(toggleBtn, link.firstChild); 

      // click event logic
      toggleBtn.addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();

        const isOpen = parentItem.classList.toggle("open");
        submenu.style.display = isOpen ? "block" : "none";
        guideLine.style.display = isOpen ? "block" : "none";

        toggleBtn.style.transform = isOpen
          ? "translateY(-50%) rotate(45deg)"
          : "translateY(-50%) rotate(0deg)";
      });
    }
  });
}

document$.subscribe(function () {
  initTOCCollapse();
});

// jupyter output collapse
document$.subscribe(() => {
  document.querySelectorAll('.jp-Cell-outputCollapser').forEach(collapser => {
    collapser.classList.add('collapse-btn');
    
    const line = document.createElement('span');
    line.className = 'line';
    collapser.appendChild(line);

    collapser.addEventListener('click', function() {
      const outputArea = this.closest('.jp-Cell').querySelector('.jp-OutputArea');
      const isExpanding = !outputArea.classList.contains('is-expanded');

      this.classList.toggle('is-expanded', isExpanding);
      outputArea.classList.toggle('is-expanded', isExpanding);
      
      // control output height
      outputArea.style.maxHeight = isExpanding ? '500px' : '0';
    });
  });
});