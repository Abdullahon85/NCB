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

      // обновляем все поля тегов (включая inline)
      document.querySelectorAll('select[id$="-tags"]').forEach((tagSelect) => {
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
      });

      // обновляем поля group_name (TagName) - фильтруем только нужные
      document
        .querySelectorAll('select[id$="-group_name"]')
        .forEach((groupNameSelect) => {
          const currentValue = groupNameSelect.value;
          groupNameSelect.innerHTML = "";
          const emptyOption = document.createElement("option");
          emptyOption.value = "";
          emptyOption.textContent = "---------";
          groupNameSelect.appendChild(emptyOption);
          data.tag_names.forEach((tn) => {
            const option = document.createElement("option");
            option.value = tn.id;
            option.textContent = tn.name;
            groupNameSelect.appendChild(option);
          });
          if (data.tag_names.some((tn) => tn.id == currentValue)) {
            groupNameSelect.value = currentValue;
          }
        });

      // обновляем поля value (FeatureValue) - фильтруем по характеристике
      document
        .querySelectorAll('select[id$="-value"]')
        .forEach((valueSelect) => {
          const currentValue = valueSelect.value;
          valueSelect.innerHTML = "";
          const emptyOption = document.createElement("option");
          emptyOption.value = "";
          emptyOption.textContent = "---------";
          valueSelect.appendChild(emptyOption);
          data.feature_values.forEach((fv) => {
            const option = document.createElement("option");
            option.value = fv.id;
            option.textContent = fv.value;
            valueSelect.appendChild(option);
          });
          if (data.feature_values.some((fv) => fv.id == currentValue)) {
            valueSelect.value = currentValue;
          }
        });
    } catch (err) {
      console.error("Ошибка при обновлении:", err);
    }
  }

  categorySelect.addEventListener("change", function () {
    if (this.value) {
      updateFeatureAndTagOptions(this.value);
    }
  });

  // Инициализация при загрузке страницы
  if (categorySelect.value) {
    updateFeatureAndTagOptions(categorySelect.value);
  }
});
