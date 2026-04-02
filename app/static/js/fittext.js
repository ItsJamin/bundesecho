/**
 * Shrinks the font size of `.fit-text` elements in `.fit-text-wrapper`
 * so they fit inside the remaining vertical space of `.quote-box`.
 * After fitting, the second `.fit-text` (context) is scaled to 75% of the width of the first.
 */
function fitTextInBox(quoteBox) {
  const wrapper = quoteBox.querySelector('.fit-text-wrapper');
  if (!wrapper) return;

  const texts = wrapper.querySelectorAll('.fit-text');
  if (texts.length === 0) return;

  // Calculate how much space is left after all non-text elements
  const totalHeight = quoteBox.clientHeight;
  let occupied = 0;

  quoteBox.childNodes.forEach(child => {
    if (child !== wrapper && child.nodeType === 1) {
      occupied += child.offsetHeight;
    }
  });

  const available = totalHeight - occupied;

  // Binary search for best fitting font size
  let low = 8, high = 25, best = low;

  while (high - low > 0.5) {
    const mid = (low + high) / 2;
    texts.forEach(el => el.style.fontSize = mid + 'px');

    if (wrapper.scrollHeight <= available) {
      best = mid;
      low = mid;
    } else {
      high = mid;
    }
  }

  // Apply best font size to all
  if (texts.length >= 1) {
  texts[0].style.fontSize = best + 'px';
  }
  if (texts.length >= 2) {
    texts[1].style.fontSize = (best * 0.75) + 'px';
  }
}

function fitAllQuotes() {
  document.querySelectorAll('.quote-box.instagram-format').forEach(fitTextInBox);
}

window.addEventListener('load', () => {
  if (document.fonts) {
    document.fonts.ready.then(fitAllQuotes);
  } else {
    fitAllQuotes();
  }
});

window.addEventListener('resize', fitAllQuotes);
