const sessionGrid = document.getElementById("sessionGrid");

const openCreateModal = document.getElementById("openCreateModal");
const closeCreateModal = document.getElementById("closeCreateModal");
const cancelCreateBtn = document.getElementById("cancelCreateBtn");
const createPanel = document.getElementById("createPanel");
const modalBackdrop = document.getElementById("modalBackdrop");
const modeSelect = document.getElementById("mode");
const locationField = document.getElementById("locationField");
const locationInput = document.getElementById("location");

bindEvents();

function bindEvents() {
  openCreateModal?.addEventListener("click", openPanel);
  closeCreateModal?.addEventListener("click", closePanel);
  cancelCreateBtn?.addEventListener("click", closePanel);
  modalBackdrop?.addEventListener("click", closePanel);
  modeSelect?.addEventListener("change", updateLocationRequirement);
  sessionGrid?.addEventListener("click", handleSessionCardClick);

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closePanel();
    }
  });

  updateLocationRequirement();
}

function openPanel() {
  createPanel?.classList.add("open");
  modalBackdrop?.classList.add("show");
  createPanel?.setAttribute("aria-hidden", "false");
  openCreateModal?.setAttribute("aria-expanded", "true");
}

function closePanel() {
  createPanel?.classList.remove("open");
  modalBackdrop?.classList.remove("show");
  createPanel?.setAttribute("aria-hidden", "true");
  openCreateModal?.setAttribute("aria-expanded", "false");
}

function handleSessionCardClick(event) {
  const interactiveElement = event.target.closest(
    "a, button, form, input, select, textarea, label"
  );

  if (interactiveElement) {
    return;
  }

  const card = event.target.closest(".session-card");
  if (card?.dataset.url) {
    window.location.href = card.dataset.url;
  }
}

function updateLocationRequirement() {
  const needsLocation = modeSelect?.value === "in-person" || modeSelect?.value === "hybrid";

  if (locationField) {
    locationField.hidden = !needsLocation;
  }

  if (locationInput) {
    locationInput.required = Boolean(needsLocation);
    if (!needsLocation) {
      locationInput.value = "";
    }
  }
}
