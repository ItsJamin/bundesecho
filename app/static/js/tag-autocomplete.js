// --- TAG AUTOCOMPLETE ---
document.addEventListener('DOMContentLoaded', () => {
  const tagsInput = document.getElementById('tags-input');
  const tagSuggestions = document.getElementById('tag-suggestions');
  const selectedTagsContainer = document.getElementById('selected-tags');
  const hiddenTagsInput = document.getElementById('tags-hidden');

  let selectedTags = [];
  let highlightedIndex = -1; 
  let currentSuggestions = []; 

  const initialTags = hiddenTagsInput.value.split(',').map(t => t.trim()).filter(t => t);
  initialTags.forEach(tag => addTag(tag));

  tagsInput.addEventListener('input', async () => {
    const query = tagsInput.value.trim();
    highlightedIndex = -1; 

    if (!query) {
      clearSuggestions();
      return;
    }

    const res = await fetch(`/api/tag?q=${encodeURIComponent(query)}`);
    const suggestions = await res.json();
    
    currentSuggestions = suggestions.filter(item => !selectedTags.includes(item.text));
    renderSuggestions();
  });

  function renderSuggestions() {
    tagSuggestions.innerHTML = '';
    currentSuggestions.forEach((item, index) => {
      const li = document.createElement('li');
      li.textContent = item.text;
      
      if (index === highlightedIndex) {
        li.classList.add('active-suggestion');
      }

      li.addEventListener('click', () => {
        addTag(item.text);
        clearSuggestions();
      });
      tagSuggestions.appendChild(li);
    });
  }

  function clearSuggestions() {
    tagSuggestions.innerHTML = '';
    currentSuggestions = [];
    highlightedIndex = -1;
    tagsInput.value = '';
  }

  tagsInput.addEventListener('keydown', (e) => {
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
    } else if (e.key === 'Enter' || e.key === 'Tab') {
      // Tab takes the first suggestion, Enter takes highlighted
      if (e.key === 'Tab' && currentSuggestions.length > 0) {
        e.preventDefault();
        highlightedIndex = 0;
        addTag(currentSuggestions[highlightedIndex].text);
        clearSuggestions();
        tagsInput.focus();
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (highlightedIndex >= 0 && currentSuggestions[highlightedIndex]) {
          addTag(currentSuggestions[highlightedIndex].text);
          clearSuggestions();
        } else {
          const query = tagsInput.value.trim();
          if (query && !selectedTags.includes(query)) {
            addTag(query);
            clearSuggestions();
          }
        }
      }
    } else if (e.key === ',') {
      e.preventDefault();
      const value = tagsInput.value.trim();
      if (value && !selectedTags.includes(value)) {
        addTag(value);
        tagsInput.value = '';
        tagSuggestions.innerHTML = '';
      }
    }
  });

  function updateHighlight() {
    renderSuggestions();
    const items = tagSuggestions.querySelectorAll('li');
    const activeItem = items[highlightedIndex];
    if (activeItem) {
      activeItem.scrollIntoView({
        block: 'nearest',
        behavior: 'smooth'
      });
    }
  }

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
      clearSuggestions();
    }
  });
});