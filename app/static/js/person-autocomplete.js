// --- PERSON AUTOCOMPLETE ---
const personInput = document.getElementById('person');
const personSuggestions = document.getElementById('person-suggestions');

let highlightedIndex = -1;
let currentSuggestions = [];

personInput.addEventListener('input', async () => {
  const query = personInput.value.trim();
  highlightedIndex = -1;

  if (!query) {
    clearSuggestions();
    return;
  }

  const res = await fetch(`/api/person?q=${encodeURIComponent(query)}`);
  const suggestions = await res.json();

  currentSuggestions = suggestions;
  
  renderSuggestions();
});

personInput.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowDown') {
    e.preventDefault();
    if (currentSuggestions.length > 0) {
      highlightedIndex = (highlightedIndex + 1) % currentSuggestions.length;
      updateHighlight();
    }
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    if (currentSuggestions.length > 0) {
      highlightedIndex = (highlightedIndex - 1 + currentSuggestions.length) % currentSuggestions.length;
      updateHighlight();
    }
  } else if (e.key === 'Tab') {
    if (currentSuggestions.length > 0) {
      e.preventDefault();
      highlightedIndex = 0;
      selectSuggestion(currentSuggestions[highlightedIndex].text);
    }
  } else if (e.key === 'Enter') {
    e.preventDefault();
    if (highlightedIndex >= 0 && currentSuggestions[highlightedIndex]) {
      selectSuggestion(currentSuggestions[highlightedIndex].text);
    }
  }
});

function renderSuggestions() {
  personSuggestions.innerHTML = '';
  currentSuggestions.forEach((item, index) => {
    const li = document.createElement('li');
    li.textContent = item.text;

    if (index === highlightedIndex) {
      li.classList.add('active-suggestion');
    }

    li.addEventListener('click', () => {
      selectSuggestion(item.text);
    });
    personSuggestions.appendChild(li);
  });
}

function updateHighlight() {
  renderSuggestions();
  const items = personSuggestions.querySelectorAll('li');
  const activeItem = items[highlightedIndex];
  if (activeItem) {
    activeItem.scrollIntoView({
      block: 'nearest',
      behavior: 'smooth'
    });
  }
}

function selectSuggestion(text) {
  personInput.value = text;
  clearSuggestions();
}

function clearSuggestions() {
  personSuggestions.innerHTML = '';
  currentSuggestions = [];
  highlightedIndex = -1;
}

document.addEventListener('click', (e) => {
  if (!personSuggestions.contains(e.target) && e.target !== personInput) {
    clearSuggestions();
  }
});
