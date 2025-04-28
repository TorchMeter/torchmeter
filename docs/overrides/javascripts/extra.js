// click to enlarge image
document.querySelectorAll('.zoom').forEach(item => {
  item.addEventListener('click', function () {
      this.classList.toggle('image-zoom-large');
  })
});

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