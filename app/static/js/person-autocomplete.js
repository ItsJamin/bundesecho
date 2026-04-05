// --- PERSON AUTOCOMPLETE ---
const personInput = document.getElementById('person');
const personSuggestions = document.getElementById('person-suggestions');

personInput.addEventListener('input', async () => {
  const query = personInput.value.trim();
  if (!query) {
    personSuggestions.innerHTML = '';
    return;
  }

  const res = await fetch(`/api/person?q=${encodeURIComponent(query)}`);
  const suggestions = await res.json();

  personSuggestions.innerHTML = '';
  suggestions.forEach(item => {
    const li = document.createElement('li');
    li.textContent = item.text;
    li.addEventListener('click', () => {
      personInput.value = item.text;
      personSuggestions.innerHTML = '';
    });
    personSuggestions.appendChild(li);
  });
});

document.addEventListener('click', (e) => {
  if (!personSuggestions.contains(e.target) && e.target !== personInput) {
    personSuggestions.innerHTML = '';
  }
});
