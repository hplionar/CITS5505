// =========================
// FORUM PAGE INTERACTIONS
// =========================
//
// Jinja-rendered version:
// - Flask/Jinja renders the thread cards.
// - This file only handles dropdowns, expand/collapse, like, and save.
// - No mock data. No API feed rendering. No infinite scroll.

document.addEventListener("DOMContentLoaded", function () {
  const feed = document.querySelector("#forumFeed");
  const dropdowns = document.querySelectorAll("[data-dropdown]");

  initialiseDropdowns(dropdowns);
  initialiseViewPlaceholder(feed);
  initialiseThreadCards(feed);
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
        viewLabel.textContent = selectedView === "categories" ? "Categories" : "Explore";
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