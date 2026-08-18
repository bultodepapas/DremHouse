(() => {
  'use strict';

  const dataNode = document.getElementById('showcase-data');
  if (!dataNode) return;

  const data = JSON.parse(dataNode.textContent);
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const formatNumber = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 });

  const setText = (field, value) => {
    document.querySelectorAll(`[data-field="${field}"]`).forEach((node) => {
      node.textContent = value;
    });
  };

  const dimensions = data.dimensions;
  setText('status', data.status);
  setText('version', data.version);
  setText('date', data.date);
  setText('phase', data.phase);
  setText('blocker', data.blocker);
  setText(
    'footprint',
    `${formatNumber.format(dimensions.width)} × ${formatNumber.format(dimensions.depth)} m`,
  );
  setText('pb-area', `${formatNumber.format(dimensions.pb_area)} m²`);
  setText('p2-area', `≈${formatNumber.format(dimensions.p2_area)} m²`);
  setText('total-area', `≈${formatNumber.format(dimensions.total_area)} m²`);
  setText('documents', formatNumber.format(data.counts.documents));
  setText('sheets', formatNumber.format(data.counts.current_sheets));
  setText('decisions', formatNumber.format(data.counts.decisions));

  const nav = document.getElementById('gallery-nav');
  const stage = document.querySelector('[data-gallery-stage]');
  const image = document.querySelector('[data-gallery-image]');
  const eyebrow = document.querySelector('[data-gallery-eyebrow]');
  const title = document.querySelector('[data-gallery-title]');
  const summary = document.querySelector('[data-gallery-summary]');
  const sourceLink = document.querySelector('[data-gallery-link]');
  const historyLink = document.querySelector('[data-gallery-history]');
  const dialog = document.querySelector('[data-dialog]');
  const dialogImage = document.querySelector('[data-dialog-image]');
  const dialogOpen = document.querySelector('[data-dialog-open]');
  const zoomViewport = document.querySelector('[data-zoom-viewport]');
  const zoomLevel = document.querySelector('[data-zoom-level]');
  let selectedIndex = 0;
  let scale = 1;
  let translateX = 0;
  let translateY = 0;
  let dragOrigin = null;

  const renderZoom = () => {
    dialogImage.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
    zoomLevel.value = `${Math.round(scale * 100)}%`;
    zoomViewport.classList.toggle('is-zoomed', scale > 1);
  };

  const resetZoom = () => {
    scale = 1;
    translateX = 0;
    translateY = 0;
    renderZoom();
  };

  const changeZoom = (nextScale, clientX, clientY) => {
    const previousScale = scale;
    scale = Math.min(8, Math.max(1, nextScale));
    if (scale === 1) {
      translateX = 0;
      translateY = 0;
    } else if (clientX !== undefined && clientY !== undefined) {
      const bounds = zoomViewport.getBoundingClientRect();
      const offsetX = clientX - bounds.left - bounds.width / 2;
      const offsetY = clientY - bounds.top - bounds.height / 2;
      const ratio = scale / previousScale;
      translateX = offsetX - (offsetX - translateX) * ratio;
      translateY = offsetY - (offsetY - translateY) * ratio;
    }
    renderZoom();
  };

  const selectItem = (index, moveFocus = false) => {
    selectedIndex = (index + data.gallery.length) % data.gallery.length;
    const item = data.gallery[selectedIndex];
    stage.classList.add('is-changing');

    window.setTimeout(
      () => {
        image.src = item.src;
        image.alt = item.alt;
        eyebrow.textContent = `${item.eyebrow} · ${item.revision}`;
        title.textContent = item.title;
        summary.textContent = item.summary;
        sourceLink.href = item.href;
        historyLink.href = item.source_href;
        dialogImage.src = item.src;
        dialogImage.alt = `${item.alt}, enlarged`;
        dialogOpen.href = item.href;
        resetZoom();
        stage.classList.remove('is-changing');
      },
      reducedMotion ? 0 : 140,
    );

    nav.querySelectorAll('button').forEach((button, buttonIndex) => {
      const active = buttonIndex === selectedIndex;
      button.setAttribute('aria-selected', String(active));
      button.tabIndex = active ? 0 : -1;
      if (active) stage.setAttribute('aria-labelledby', button.id);
      if (active && moveFocus) button.focus();
    });
  };

  data.gallery.forEach((item, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.index = String(index + 1).padStart(2, '0');
    button.setAttribute('role', 'tab');
    button.id = `gallery-tab-${index + 1}`;
    button.setAttribute('aria-controls', 'gallery-panel');
    button.setAttribute('aria-selected', 'false');
    button.innerHTML = `<strong>${item.title}</strong><span>${item.eyebrow}</span>`;
    button.addEventListener('click', () => selectItem(index));
    button.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowDown' || event.key === 'ArrowRight') {
        event.preventDefault();
        selectItem(index + 1, true);
      }
      if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') {
        event.preventDefault();
        selectItem(index - 1, true);
      }
    });
    nav.append(button);
  });
  selectItem(0);

  document.querySelector('[data-open-dialog]').addEventListener('click', () => {
    resetZoom();
    if (typeof dialog.showModal === 'function') dialog.showModal();
  });
  document.querySelector('[data-close-dialog]').addEventListener('click', () => dialog.close());
  document.querySelector('[data-zoom-in]').addEventListener('click', () => changeZoom(scale * 1.5));
  document.querySelector('[data-zoom-out]').addEventListener('click', () => changeZoom(scale / 1.5));
  document.querySelector('[data-zoom-reset]').addEventListener('click', resetZoom);
  zoomViewport.addEventListener(
    'wheel',
    (event) => {
      event.preventDefault();
      changeZoom(scale * (event.deltaY < 0 ? 1.2 : 1 / 1.2), event.clientX, event.clientY);
    },
    { passive: false },
  );
  zoomViewport.addEventListener('dblclick', (event) => {
    changeZoom(scale > 1 ? 1 : 2, event.clientX, event.clientY);
  });
  zoomViewport.addEventListener('pointerdown', (event) => {
    if (scale === 1) return;
    dragOrigin = { x: event.clientX - translateX, y: event.clientY - translateY };
    zoomViewport.setPointerCapture(event.pointerId);
    zoomViewport.classList.add('is-dragging');
  });
  zoomViewport.addEventListener('pointermove', (event) => {
    if (!dragOrigin) return;
    translateX = event.clientX - dragOrigin.x;
    translateY = event.clientY - dragOrigin.y;
    renderZoom();
  });
  const endDrag = (event) => {
    if (!dragOrigin) return;
    dragOrigin = null;
    zoomViewport.classList.remove('is-dragging');
    if (zoomViewport.hasPointerCapture(event.pointerId)) {
      zoomViewport.releasePointerCapture(event.pointerId);
    }
  };
  zoomViewport.addEventListener('pointerup', endDrag);
  zoomViewport.addEventListener('pointercancel', endDrag);
  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) dialog.close();
  });
  dialog.addEventListener('close', resetZoom);

  if (!reducedMotion) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 },
    );
    document.querySelectorAll('[data-reveal]').forEach((node) => observer.observe(node));
  } else {
    document.querySelectorAll('[data-reveal]').forEach((node) => node.classList.add('is-visible'));
  }

  const header = document.querySelector('[data-header]');
  const heroArt = document.querySelector('[data-hero-art]');
  let ticking = false;
  const updateScroll = () => {
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    const progress = maxScroll > 0 ? (window.scrollY / maxScroll) * 100 : 0;
    document.documentElement.style.setProperty('--progress', `${progress}%`);
    header.classList.toggle('is-scrolled', window.scrollY > 24);
    if (!reducedMotion && window.scrollY < window.innerHeight) {
      heroArt.style.setProperty('--hero-shift', `${Math.min(window.scrollY * 0.09, 54)}px`);
    }
    ticking = false;
  };
  window.addEventListener(
    'scroll',
    () => {
      if (!ticking) {
        window.requestAnimationFrame(updateScroll);
        ticking = true;
      }
    },
    { passive: true },
  );
  updateScroll();
})();
