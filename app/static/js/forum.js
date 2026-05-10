// =========================
// FORUM PAGE INTERACTIONS
// =========================
//
// Jinja-rendered version:
// - Flask/Jinja renders the thread cards.
// - This file only handles UI behaviour.
// - No mock thread data is generated here.

document.addEventListener("DOMContentLoaded", function () {
  const feed = document.querySelector("#forumFeed");
  const dropdowns = document.querySelectorAll("[data-dropdown]");

  initialiseDropdowns(dropdowns);
  initialiseViewPlaceholder(feed);
  initialiseThreadCards(feed);
  initialiseCreateThreadPanel();
  initialiseCreateThreadForm();
});


// =========================
// Dropdown behaviour
// =========================

function initialiseDropdowns(dropdowns) {
  dropdowns.forEach(function (dropdown) {
    const toggle = dropdown.querySelector("[data-dropdown-toggle]");
    const menu = dropdown.querySelector("[data-dropdown-menu]");

    if (!toggle || !menu) return;

    toggle.addEventListener("click", function (event) {
      event.stopPropagation();

      const isOpen = !menu.hidden;

      closeAllDropdowns(dropdowns);

      menu.hidden = isOpen;
      toggle.setAttribute("aria-expanded", String(!isOpen));
    });

    menu.addEventListener("click", function (event) {
      event.stopPropagation();
    });
  });

  document.addEventListener("click", function () {
    closeAllDropdowns(dropdowns);
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeAllDropdowns(dropdowns);
    }
  });
}


function closeAllDropdowns(dropdowns) {
  dropdowns.forEach(function (dropdown) {
    const toggle = dropdown.querySelector("[data-dropdown-toggle]");
    const menu = dropdown.querySelector("[data-dropdown-menu]");

    if (!toggle || !menu) return;

    menu.hidden = true;
    toggle.setAttribute("aria-expanded", "false");
  });
}


// =========================
// View placeholder
// =========================

function initialiseViewPlaceholder(feed) {
  const viewButtons = document.querySelectorAll("[data-view-option]");
  const viewLabel = document.querySelector("[data-view-label]");

  viewButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      const selectedView = button.dataset.viewOption;

      viewButtons.forEach(function (item) {
        item.classList.remove("is-active");
      });

      button.classList.add("is-active");

      if (viewLabel) {
        viewLabel.textContent = selectedView === "categories"
          ? "Categories"
          : "Explore";
      }

      if (selectedView === "categories") {
        showCategoryPlaceholder(feed);
      } else {
        window.location.href = "/forum";
      }
    });
  });
}


function showCategoryPlaceholder(feed) {
  if (!feed) return;

  feed.innerHTML = `
    <div class="forum-placeholder-card">
      <p class="forum-placeholder-title">Category view will be added next.</p>
      <p class="forum-placeholder-text">
        For now, this screen focuses on the Explore feed.
      </p>
    </div>
  `;
}


// =========================
// Thread card interactions
// =========================

function initialiseThreadCards(feed) {
  if (!feed) return;

  feed.addEventListener("click", function (event) {
    const expandButton = event.target.closest("[data-expand-thread]");
    const likeButton = event.target.closest("[data-like-thread]");
    const saveButton = event.target.closest("[data-save-thread]");

    if (expandButton) {
      toggleThreadExpansion(expandButton);
      return;
    }

    if (likeButton) {
      toggleThreadLike(likeButton);
      return;
    }

    if (saveButton) {
      toggleThreadSave(saveButton);
    }
  });
}


function toggleThreadExpansion(button) {
  const card = button.closest(".thread-card");
  if (!card) return;

  const body = card.querySelector(".thread-body");
  const icon = button.querySelector("i");

  const isExpanded = button.getAttribute("aria-expanded") === "true";
  const nextExpanded = !isExpanded;

  button.setAttribute("aria-expanded", String(nextExpanded));
  button.setAttribute(
    "aria-label",
    nextExpanded ? "Collapse thread" : "Expand thread"
  );

  card.classList.toggle("is-expanded", nextExpanded);

  if (body) {
    body.hidden = !nextExpanded;
  }

  if (icon) {
    icon.className = nextExpanded
      ? "bi bi-x-lg"
      : "bi bi-arrows-angle-expand";
  }
}


async function toggleThreadLike(button) {
  const card = button.closest(".thread-card");
  const threadId = card?.dataset.threadId;
  const countElement = button.querySelector("[data-like-count]");
  const icon = button.querySelector("i");

  if (!threadId || !countElement || !icon) return;

  button.disabled = true;

  try {
    const response = await fetch(`/forum/thread/${threadId}/like`, {
      method: "POST",
      headers: buildAjaxHeaders()
    });

    if (!response.ok) {
      throw new Error("Failed to update thread like");
    }

    const data = await response.json();
    const isLiked = Boolean(data.liked);

    button.classList.toggle("is-liked", isLiked);
    button.setAttribute("aria-pressed", String(isLiked));

    icon.className = isLiked
      ? "bi bi-hand-thumbs-up-fill"
      : "bi bi-hand-thumbs-up";

    countElement.textContent = String(data.likeCount ?? 0);
  } catch (error) {
    console.error("Failed to update thread like:", error);
  } finally {
    button.disabled = false;
  }
}


async function toggleThreadSave(button) {
  const card = button.closest(".thread-card");
  const threadId = card?.dataset.threadId;
  const icon = button.querySelector("i");

  if (!threadId || !icon) return;

  button.disabled = true;

  try {
    const response = await fetch(`/forum/thread/${threadId}/save`, {
      method: "POST",
      headers: buildAjaxHeaders()
    });

    if (!response.ok) {
      throw new Error("Failed to update saved thread");
    }

    const data = await response.json();
    const isSaved = Boolean(data.saved);

    button.classList.toggle("is-saved", isSaved);
    button.setAttribute("aria-pressed", String(isSaved));
    button.setAttribute("aria-label", isSaved ? "Unsave thread" : "Save thread");

    icon.className = isSaved ? "bi bi-bookmark-fill" : "bi bi-bookmark";
  } catch (error) {
    console.error("Failed to update saved thread:", error);
  } finally {
    button.disabled = false;
  }
}


// =========================
// AJAX helpers
// =========================

function buildAjaxHeaders() {
  const headers = {
    "X-Requested-With": "XMLHttpRequest"
  };

  const csrfToken = getCsrfToken();

  if (csrfToken) {
    headers["X-CSRFToken"] = csrfToken;
  }

  return headers;
}


function getCsrfToken() {
  const metaToken = document.querySelector('meta[name="csrf-token"]');
  const inputToken = document.querySelector('input[name="csrf_token"]');

  return metaToken?.content || inputToken?.value || "";
}


// =========================
// Create thread side panel
// =========================

function initialiseCreateThreadPanel() {
  const openButton = document.querySelector(
    "#openCreateThreadPanel, #create-thread-link"
  );

  const closeButton = document.querySelector("#closeCreateThreadPanel");
  const cancelButton = document.querySelector("#cancelCreateThreadPanel");
  const panel = document.querySelector("#createThreadPanel");
  const backdrop = document.querySelector("#forumModalBackdrop");

  if (!openButton || !panel || !backdrop) return;

  function openPanel(event) {
    if (event) {
      event.preventDefault();
    }

    panel.setAttribute("aria-hidden", "false");
    openButton.setAttribute("aria-expanded", "true");
    document.body.classList.add("forum-panel-open");

    requestAnimationFrame(function () {
      panel.classList.add("is-open");
      backdrop.classList.add("is-visible");
    });
  }

  function closePanel() {
    panel.classList.remove("is-open");
    backdrop.classList.remove("is-visible");

    openButton.setAttribute("aria-expanded", "false");
    document.body.classList.remove("forum-panel-open");

    window.setTimeout(function () {
      if (!panel.classList.contains("is-open")) {
        panel.setAttribute("aria-hidden", "true");
      }
    }, 200);
  }

  openButton.addEventListener("click", openPanel);
  backdrop.addEventListener("click", closePanel);

  if (closeButton) {
    closeButton.addEventListener("click", closePanel);
  }

  if (cancelButton) {
    cancelButton.addEventListener("click", closePanel);
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && panel.classList.contains("is-open")) {
      closePanel();
    }
  });
}


// =========================
// Create thread form validation
// =========================

function initialiseCreateThreadForm() {
  const form = document.querySelector("#create-thread-form");

  if (!form) return;

  const titleInput = form.querySelector("#thread-title");
  const bodyInput = form.querySelector("#thread-body");
  const titleCount = form.querySelector("#threadTitleCount");
  const tagsToggle = form.querySelector("#toggleThreadTags");
  const tagsField = form.querySelector("#threadTagsField");
  const tagsInput = form.querySelector("#thread-tags");

  setupTitleInput(titleInput, titleCount);
  setupTagsToggle(tagsToggle, tagsField, tagsInput);
  setupRequiredField(titleInput);
  setupRequiredField(bodyInput);

  form.addEventListener("submit", function (event) {
    const titleIsValid = validateRequiredForumField(
      titleInput,
      "The title is required and cannot be empty."
    );

    const bodyIsValid = validateRequiredForumField(
      bodyInput,
      "The message is required and cannot be empty."
    );

    if (!titleIsValid || !bodyIsValid) {
      event.preventDefault();

      const firstInvalid = form.querySelector(
        ".forum-field.is-invalid input, .forum-field.is-invalid textarea"
      );

      if (firstInvalid) {
        firstInvalid.focus();
      }
    }
  });
}


function setupTitleInput(titleInput, titleCount) {
  if (!titleInput) return;

  titleInput.setAttribute("maxlength", "100");
  updateTitleCount(titleInput, titleCount);

  titleInput.addEventListener("input", function () {
    updateTitleCount(titleInput, titleCount);
  });
}


function setupTagsToggle(tagsToggle, tagsField, tagsInput) {
  if (!tagsToggle || !tagsField) return;

  tagsToggle.addEventListener("click", function () {
    const shouldShow = tagsField.hidden;

    tagsField.hidden = !shouldShow;
    tagsToggle.setAttribute("aria-expanded", String(shouldShow));

    if (shouldShow && tagsInput) {
      tagsInput.focus();
    }
  });
}


function setupRequiredField(input) {
  if (!input) return;

  input.addEventListener("input", function () {
    const field = input.closest("[data-required-field]");

    if (field && field.classList.contains("is-invalid")) {
      validateRequiredForumField(input, "");
    }
  });

  input.addEventListener("blur", function () {
    const field = input.closest("[data-required-field]");

    if (field && field.classList.contains("is-invalid")) {
      validateRequiredForumField(input, "");
    }
  });
}


function validateRequiredForumField(input, message) {
  if (!input) return true;

  const field = input.closest("[data-required-field]");
  const feedback = field ? field.querySelector(".forum-field-feedback") : null;
  const isValid = input.value.trim().length > 0;

  if (!field) return isValid;

  field.classList.toggle("is-invalid", !isValid);
  field.classList.toggle("is-valid", isValid);

  if (feedback) {
    feedback.textContent = !isValid ? message : "";
  }

  return isValid;
}


function updateTitleCount(input, countElement) {
  if (!input || !countElement) return;

  const maxLength = Number(input.getAttribute("maxlength")) || 100;
  const currentLength = input.value.length;

  countElement.textContent = `${currentLength}/${maxLength}`;
}