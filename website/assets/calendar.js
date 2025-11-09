function filterEvents() {
  const categorySelect = document.getElementById("categoryFilter");
  const searchInput = document.getElementById("searchInput");

  const selectedCategories = Array.from(categorySelect.selectedOptions).map(opt => opt.value);
  const searchText = searchInput.value.toLowerCase();

  const events = document.querySelectorAll(".event");

  events.forEach(event => {
    const eventCategory = event.dataset.category ? event.dataset.category.toLowerCase() : "";
    const eventTitle = event.textContent.toLowerCase();

    // Condición de categoría
    const categoryMatch =
      selectedCategories.includes("all") ||
      selectedCategories.length === 0 ||
      selectedCategories.includes(eventCategory);

    // Condición de texto
    const textMatch = eventTitle.includes(searchText);

    // Mostrar u ocultar
    if (categoryMatch && textMatch) {
      event.style.display = "";
    } else {
      event.style.display = "none";
    }
  });
}