document.addEventListener("DOMContentLoaded", () => {
  // ----- PERSON AUTOCOMPLETE -----
  const personInput = document.getElementById("person-input");
  const personSuggestions = document.getElementById("person-suggestions");
  const personIdInput = document.getElementById("person-id");

  personInput.addEventListener("input", async () => {
    const query = personInput.value.trim();
    if (!query) {
      personSuggestions.innerHTML = "";
      personSuggestions.style.display = "none";
      personIdInput.value = "";
      return;
    }

    try {
      const res = await fetch(`/api/person?q=${encodeURIComponent(query)}`);
      if (!res.ok) throw new Error("Network error");

      const data = await res.json();
      if (!data.length) {
        personSuggestions.innerHTML = "";
        personSuggestions.style.display = "none";
        return;
      }

      personSuggestions.innerHTML = "";
      data.forEach(item => {
        const li = document.createElement("li");
        li.textContent = item.text;
        li.tabIndex = 0;

        li.addEventListener("mousedown", e => {
          e.preventDefault();
          personInput.value = item.text;
          personIdInput.value = item.id;
          personSuggestions.innerHTML = "";
          personSuggestions.style.display = "none";
        });

        personSuggestions.appendChild(li);
      });

      personSuggestions.style.display = "block";
    } catch (error) {
      personSuggestions.innerHTML = "";
      personSuggestions.style.display = "none";
      console.error(error);
    }
  });

  document.addEventListener("click", e => {
    if (!personSuggestions.contains(e.target) && e.target !== personInput) {
      personSuggestions.style.display = "none";
    }
  });

  // ----- TAG AUTOCOMPLETE -----
  const tagInput = document.getElementById("tag-input");
  const tagSuggestions = document.getElementById("tag-suggestions");
  const selectedTagsContainer = document.getElementById("selected-tags");
  const searchForm = document.getElementById("search-form");

  let selectedTags = [...selectedTagsContainer.children].map(tagEl => ({
    id: tagEl.dataset.id,
    text: tagEl.textContent.replace("×", "").trim(),
    negative: tagEl.dataset.negative === "true"
  }));

  function updateTagHiddenInputs() {
    [...searchForm.querySelectorAll('input[name="tags"], input[name="tags_neg"]')].forEach(input => input.remove());

    selectedTags.forEach(tag => {
      const input = document.createElement("input");
      input.type = "hidden";
      input.value = tag.id;
      input.name = tag.negative ? "tags_neg" : "tags";
      searchForm.appendChild(input);
    });
  }

  function renderSelectedTags() {
    selectedTagsContainer.innerHTML = "";
    selectedTags.forEach(tag => {
      const div = document.createElement("div");
      div.className = "selected-tag";
      if(tag.negative) div.classList.add("selected-tag-negative");
      div.dataset.id = tag.id;
      div.textContent = tag.text + " ";

      const removeSpan = document.createElement("span");
      removeSpan.className = "remove-tag";
      removeSpan.textContent = "×";
      removeSpan.title = "Remove tag";
      removeSpan.addEventListener("click", () => {
        selectedTags = selectedTags.filter(t => t.id !== tag.id);
        renderSelectedTags();
        updateTagHiddenInputs();
      });

      div.addEventListener("click", (e) => {
        if(e.target !== removeSpan){
          tag.negative = !tag.negative;
          renderSelectedTags();
          updateTagHiddenInputs();
        }
      });

      div.appendChild(removeSpan);
      selectedTagsContainer.appendChild(div);
    });
  }

  async function fetchTagSuggestions(query) {
    if (!query) {
      tagSuggestions.innerHTML = "";
      tagSuggestions.style.display = "none";
      return;
    }

    try {
      const res = await fetch(`/api/tag?q=${encodeURIComponent(query)}`);
      if (!res.ok) throw new Error("Network error");

      const data = await res.json();
      const filtered = data.filter(item => !selectedTags.some(tag => tag.id === item.id));

      if (!filtered.length) {
        tagSuggestions.innerHTML = "";
        tagSuggestions.style.display = "none";
        return;
      }

      tagSuggestions.innerHTML = "";
      filtered.forEach(item => {
        const li = document.createElement("li");
        li.textContent = item.text;
        li.tabIndex = 0;

        li.addEventListener("mousedown", e => {
          e.preventDefault();
          selectedTags.push(item);
          renderSelectedTags();
          updateTagHiddenInputs();
          tagInput.value = "";
          tagSuggestions.innerHTML = "";
          tagSuggestions.style.display = "none";
        });

        tagSuggestions.appendChild(li);
      });

      tagSuggestions.style.display = "block";
    } catch (error) {
      tagSuggestions.innerHTML = "";
      tagSuggestions.style.display = "none";
      console.error(error);
    }
  }

  tagInput.addEventListener("input", () => {
    fetchTagSuggestions(tagInput.value.trim());
  });

  document.addEventListener("click", e => {
    if (!tagSuggestions.contains(e.target) && e.target !== tagInput) {
      tagSuggestions.style.display = "none";
    }
  });

  updateTagHiddenInputs();
  renderSelectedTags();
});

function removeEmptyFields(event) {
    const form = event.target;
    const inputs = form.querySelectorAll('input[type="text"], input[type="date"], input[type="hidden"][name="meta_person"]');
    inputs.forEach(input => {
        if (input.value === '') {
            input.name = ''; // Remove the name so it's not submitted
        }
    });
}
