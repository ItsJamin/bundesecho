// --- TAG AUTOCOMPLETE ---
document.addEventListener('DOMContentLoaded', () => {
  const tagsInput = document.getElementById('tags-input');
  const tagSuggestions = document.getElementById('tag-suggestions');
  const selectedTagsContainer = document.getElementById('selected-tags');
  const hiddenTagsInput = document.getElementById('tags-hidden');

  let selectedTags = [];

  // --- Init existing tags from hidden input ---
  const initialTags = hiddenTagsInput.value.split(',').map(t => t.trim()).filter(t => t);
  initialTags.forEach(tag => addTag(tag));

  // --- All remaining event listeners and functions must also be inside here ---
  tagsInput.addEventListener('input', async () => {
    const query = tagsInput.value.trim();
    if (!query) {
      tagSuggestions.innerHTML = '';
      return;
    }

    const res = await fetch(`/api/tag?q=${encodeURIComponent(query)}`);
    const suggestions = await res.json();

    tagSuggestions.innerHTML = '';
    suggestions.forEach(item => {
      if (!selectedTags.includes(item.text)) {
        const li = document.createElement('li');
        li.textContent = item.text;
        li.addEventListener('click', () => {
          addTag(item.text);
          tagSuggestions.innerHTML = '';
          tagsInput.value = '';
        });
        tagSuggestions.appendChild(li);
      }
    });
  });

  tagsInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      const value = tagsInput.value.trim();
      if (value && !selectedTags.includes(value)) {
        addTag(value);
        tagsInput.value = '';
        tagSuggestions.innerHTML = '';
      }
    }
  });

  function addTag(tag) {
    selectedTags.push(tag);
    updateTagDisplay();
  }

  function removeTag(tag) {
    selectedTags = selectedTags.filter(t => t !== tag);
    updateTagDisplay();
  }

  function updateTagDisplay() {
    selectedTagsContainer.innerHTML = '';
    selectedTags.forEach(tag => {
      const span = document.createElement('span');
      span.className = 'selected-tag';
      span.innerHTML = `
        ${tag}
        <span class="remove-tag">&times;</span>
      `;
      span.querySelector('.remove-tag').addEventListener('click', () => removeTag(tag));
      selectedTagsContainer.appendChild(span);
    });
    hiddenTagsInput.value = selectedTags.join(',');
  }

  document.addEventListener('click', (e) => {
    if (!tagSuggestions.contains(e.target) && e.target !== tagsInput) {
      tagSuggestions.innerHTML = '';
    }
  });
});

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
