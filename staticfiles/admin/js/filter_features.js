document.addEventListener("DOMContentLoaded", function () {
  const categorySelect = document.querySelector("#id_category");
  if (!categorySelect) return;

  async function updateFeatureAndTagOptions(categoryId) {
    try {
      const response = await fetch(
        `/api/features-tags-by-category/?category=${categoryId}`
      );

      if (!response.ok) return;
      const data = await response.json();

      // обновляем характеристики
      document.querySelectorAll('select[id$="-feature"]').forEach((select) => {
        const currentValue = select.value;
        select.innerHTML = "";
        data.features.forEach((f) => {
          const option = document.createElement("option");
          option.value = f.id;
          option.textContent = f.name;
          select.appendChild(option);
        });
        if (data.features.some((f) => f.id == currentValue)) {
          select.value = currentValue;
        }
      });

      // обновляем теги
      const tagSelect = document.querySelector("#id_tags");
      if (tagSelect) {
        const selectedValues = Array.from(tagSelect.selectedOptions).map(
          (o) => o.value
        );
        tagSelect.innerHTML = "";
        data.tags.forEach((t) => {
          const option = document.createElement("option");
          option.value = t.id;
          option.textContent = t.name;
          tagSelect.appendChild(option);
        });
        selectedValues.forEach((v) => {
          if (data.tags.some((t) => t.id == v)) {
            tagSelect.querySelector(`option[value="${v}"]`).selected = true;
          }
        });
      }
    } catch (err) {
      console.error("Ошибка при обновлении:", err);
    }
  }

  categorySelect.addEventListener("change", function () {
    if (this.value) updateFeatureAndTagOptions(this.value);
  });

  if (categorySelect.value) {
    updateFeatureAndTagOptions(categorySelect.value);
  }
});
