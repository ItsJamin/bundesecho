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
  const searchForm = document.getElementById("search-form");

  const tagInput = document.getElementById("tag-input");
  const tagSuggestions = document.getElementById("tag-suggestions");
  const selectedTagsContainer = document.getElementById("selected-tags");
  let selectedTags = [...selectedTagsContainer.children].map(tagEl => ({
    id: tagEl.dataset.id,
    text: tagEl.textContent.replace("×", "").trim(),
    negative: tagEl.dataset.negative === "true"
  }));

  const personTagInput = document.getElementById("person-tag-input");
  const personTagSuggestions = document.getElementById("person-tag-suggestions");
  const selectedPersonTagsContainer = document.getElementById("selected-person-tags");

  let selectedPersonTags = [...selectedPersonTagsContainer.children].map(tagEl => ({
    id: tagEl.dataset.id,
    text: tagEl.textContent.replace("×", "").trim(),
    negative: tagEl.dataset.negative === "true"
  }));

  function initTagAutocomplete(options) {
    const {
      input,
      suggestions,
      selectedContainer,
      selectedArray,
      apiEndpoint,
      supportsNegative = false,
      className,
      negClassName,
      hiddenName,
      hiddenNegName
    } = options;

    function updateHiddenInputs() {
      const selectors = supportsNegative ? `input[name="${hiddenName}"], input[name="${hiddenNegName}"]` : `input[name="${hiddenName}"]`;
      [...searchForm.querySelectorAll(selectors)].forEach(input => input.remove());

      selectedArray.forEach(tag => {
        const input = document.createElement("input");
        input.type = "hidden";
        input.value = tag.id;
        input.name = supportsNegative && tag.negative ? hiddenNegName : hiddenName;
        searchForm.appendChild(input);
      });
    }

    function renderSelectedTags() {
      selectedContainer.innerHTML = "";
      selectedArray.forEach(tag => {
        const div = document.createElement("div");
        div.className = className;
        if (supportsNegative && tag.negative) div.classList.add(negClassName);
        div.dataset.id = tag.id;
        div.textContent = tag.text + " ";

        const removeSpan = document.createElement("span");
        removeSpan.className = "remove-tag";
        removeSpan.textContent = "×";
        removeSpan.title = "Remove tag";
        removeSpan.addEventListener("click", () => {
          selectedArray.splice(selectedArray.indexOf(tag), 1);
          renderSelectedTags();
          updateHiddenInputs();
        });

        if (supportsNegative) {
          div.addEventListener("click", (e) => {
            if (e.target !== removeSpan) {
              tag.negative = !tag.negative;
              renderSelectedTags();
              updateHiddenInputs();
            }
          });
        }

        div.appendChild(removeSpan);
        selectedContainer.appendChild(div);
      });
    }

    async function fetchSuggestions(query) {
      if (!query) {
        suggestions.innerHTML = "";
        suggestions.style.display = "none";
        return;
      }

      try {
        const res = await fetch(`${apiEndpoint}?q=${encodeURIComponent(query)}`);
        if (!res.ok) throw new Error("Network error");

        const data = await res.json();
        const filtered = data.filter(item => !selectedArray.some(tag => tag.id === item.id));

        if (!filtered.length) {
          suggestions.innerHTML = "";
          suggestions.style.display = "none";
          return;
        }

        suggestions.innerHTML = "";
        filtered.forEach(item => {
          const li = document.createElement("li");
          li.textContent = item.text;
          li.tabIndex = 0;

          li.addEventListener("mousedown", e => {
            e.preventDefault();
            selectedArray.push({ ...item, negative: false });
            renderSelectedTags();
            updateHiddenInputs();
            input.value = "";
            suggestions.innerHTML = "";
            suggestions.style.display = "none";
          });

          suggestions.appendChild(li);
        });

        suggestions.style.display = "block";
      } catch (error) {
        suggestions.innerHTML = "";
        suggestions.style.display = "none";
        console.error(error);
      }
    }

    input.addEventListener("input", () => {
      fetchSuggestions(input.value.trim());
    });

    document.addEventListener("click", e => {
      if (!suggestions.contains(e.target) && e.target !== input) {
        suggestions.style.display = "none";
      }
    });

    updateHiddenInputs();
    renderSelectedTags();
  }

  // Initialize tag autocomplete
  initTagAutocomplete({
    input: tagInput,
    suggestions: tagSuggestions,
    selectedContainer: selectedTagsContainer,
    selectedArray: selectedTags,
    apiEndpoint: "/api/tag",
    supportsNegative: true,
    className: "selected-tag",
    negClassName: "selected-tag-negative",
    hiddenName: "tags",
    hiddenNegName: "tags_neg"
  });

  // Initialize person tag autocomplete
  initTagAutocomplete({
    input: personTagInput,
    suggestions: personTagSuggestions,
    selectedContainer: selectedPersonTagsContainer,
    selectedArray: selectedPersonTags,
    apiEndpoint: "/api/tag",
    supportsNegative: true,
    className: "selected-tag",
    negClassName: "selected-tag-negative",
    hiddenName: "person_tags",
    hiddenNegName: "person_tags_neg"
  });
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
