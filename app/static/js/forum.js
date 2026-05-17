// =========================
// FORUM PAGE INTERACTIONS
// =========================
//
// Flask/Jinja renders the forum cards and thread detail page.
// This file only handles UI behaviour and AJAX actions.

document.addEventListener("DOMContentLoaded", function () {
  const feed = document.querySelector("#forumFeed");
  const dropdowns = document.querySelectorAll("[data-dropdown]");

  initialiseDropdowns(dropdowns);
  initialiseThreadCards(feed);
  initialiseThreadDetailActions();
  initialiseDiscussionComments();
  initialiseCreateThreadPanel();
  initialiseCreateThreadForm();
  initialiseForumInfiniteScroll();
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


function initialiseThreadDetailActions() {
  const detailPost = document.querySelector(".discussion-thread-post[data-thread-id]");

  if (!detailPost) return;

  detailPost.addEventListener("click", function (event) {
    const likeButton = event.target.closest("[data-like-thread]");
    const saveButton = event.target.closest("[data-save-thread]");
    const focusCommentButton = event.target.closest("[data-focus-comment-box]");

    if (likeButton) {
      toggleThreadLike(likeButton);
      return;
    }

    if (saveButton) {
      toggleThreadSave(saveButton);
      return;
    }

    if (focusCommentButton) {
      focusThreadCommentBox();
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
  const threadContainer = button.closest("[data-thread-id]");
  const threadId = threadContainer?.dataset.threadId;
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
  const threadContainer = button.closest("[data-thread-id]");
  const threadId = threadContainer?.dataset.threadId;
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


function focusThreadCommentBox() {
  const commentBox = document.querySelector("#thread-comment-box");

  if (!commentBox) return;

  commentBox.scrollIntoView({
    behavior: "smooth",
    block: "center"
  });

  window.setTimeout(function () {
    commentBox.focus();
  }, 250);
}


// =========================
// Thread detail comment interactions
// =========================

function initialiseDiscussionComments() {
  document.addEventListener("click", function (event) {
    const replyButton = event.target.closest("[data-reply-trigger]");
    const cancelButton = event.target.closest("[data-reply-cancel]");
    const collapseButton = event.target.closest("[data-collapse-comment]");
    const showMoreButton = event.target.closest("[data-show-more]");
    const deleteForm = event.target.closest("[data-delete-reply-form]");

    if (deleteForm) {
      const confirmed = window.confirm("Delete this comment?");

      if (!confirmed) {
        event.preventDefault();
      }

      return;
    }

    if (replyButton) {
      toggleInlineReplyForm(replyButton);
      return;
    }

    if (cancelButton) {
      closeInlineReplyForm(cancelButton);
      return;
    }

    if (collapseButton) {
      toggleCommentCollapse(collapseButton);
      return;
    }

    if (showMoreButton) {
      showMoreReplies(showMoreButton);
    }
  });
}


function toggleInlineReplyForm(button) {
  const targetId = button.dataset.replyTarget;
  const form = document.getElementById(targetId);

  if (!form) return;

  const shouldShow = form.hidden;
  form.hidden = !shouldShow;

  if (shouldShow) {
    const textarea = form.querySelector("textarea");

    if (textarea) {
      textarea.focus();
    }
  }
}


function closeInlineReplyForm(button) {
  const form = button.closest(".discussion-inline-reply-form");

  if (!form) return;

  form.hidden = true;
}


function toggleCommentCollapse(button) {
  const comment = button.closest("[data-comment-item]");

  if (!comment) return;

  const isCollapsed = comment.classList.toggle("is-collapsed");
  const icon = button.querySelector("[data-collapse-icon]");

  button.setAttribute("aria-expanded", String(!isCollapsed));

  if (icon) {
    icon.className = isCollapsed ? "bi bi-chevron-right" : "bi bi-chevron-down";
  }
}


function showMoreReplies(button) {
  const replyList = button.closest("[data-reply-list]");

  if (!replyList) return;

  replyList.classList.add("show-all");
  button.hidden = true;
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
  const tagSearchInput = form.querySelector("[data-tag-search]");

  setupTitleInput(titleInput, titleCount);
  setupTagsToggle(tagsToggle, tagsField, tagSearchInput);
  initialiseForumTagPicker(form);
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


function setupTagsToggle(tagsToggle, tagsField, focusTarget) {
  if (!tagsToggle || !tagsField) return;

  tagsToggle.addEventListener("click", function () {
    const shouldShow = tagsField.hidden;

    tagsField.hidden = !shouldShow;
    tagsToggle.setAttribute("aria-expanded", String(shouldShow));

    if (shouldShow && focusTarget) {
      focusTarget.focus();
    }
  });
}


function initialiseForumTagPicker(form) {
  const picker = form.querySelector("[data-tag-picker]");

  if (!picker) return;

  const maxTags = Number(picker.dataset.maxTags) || 3;
  const searchInput = picker.querySelector("[data-tag-search]");
  const selectedTagsContainer = picker.querySelector("[data-selected-tags]");
  const hiddenInputsContainer = picker.querySelector("[data-tag-hidden-inputs]");
  const helperText = picker.querySelector("[data-tag-helper]");
  const tagOptions = Array.from(picker.querySelectorAll("[data-tag-option]"));
  const tagsToggle = picker.querySelector("#toggleThreadTags");

  const selectedTags = new Map();

  tagOptions.forEach(function (option) {
    option.addEventListener("click", function () {
      addSelectedTag(option);
    });
  });

  if (searchInput) {
    searchInput.addEventListener("input", function () {
      filterTagOptions(searchInput.value, tagOptions);
    });
  }

  if (selectedTagsContainer) {
    selectedTagsContainer.addEventListener("click", function (event) {
      const removeButton = event.target.closest("[data-remove-selected-tag]");

      if (!removeButton) return;

      selectedTags.delete(removeButton.dataset.tagId);
      updateTagPickerUI();
    });
  }

  function addSelectedTag(option) {
    const tagId = option.dataset.tagId;
    const tagName = option.dataset.tagName;
    const tagSlug = option.dataset.tagSlug;

    if (!tagId || selectedTags.has(tagId)) return;

    if (selectedTags.size >= maxTags) {
      showTagHelper(`You can only choose up to ${maxTags} tags.`, true);
      return;
    }

    selectedTags.set(tagId, {
      id: tagId,
      name: tagName,
      slug: tagSlug
    });

    if (searchInput) {
      searchInput.value = "";
      filterTagOptions("", tagOptions);
      searchInput.focus();
    }

    updateTagPickerUI();
  }

  function updateTagPickerUI() {
    selectedTagsContainer.innerHTML = "";
    hiddenInputsContainer.innerHTML = "";

    selectedTags.forEach(function (tag) {
      const chip = document.createElement("span");
      chip.className = "forum-selected-tag";
      chip.textContent = `#${tag.slug}`;

      const removeButton = document.createElement("button");
      removeButton.type = "button";
      removeButton.className = "forum-selected-tag-remove";
      removeButton.setAttribute("aria-label", `Remove ${tag.slug} tag`);
      removeButton.setAttribute("data-remove-selected-tag", "");
      removeButton.dataset.tagId = tag.id;
      removeButton.textContent = "×";

      chip.appendChild(removeButton);
      selectedTagsContainer.appendChild(chip);

      const hiddenInput = document.createElement("input");
      hiddenInput.type = "hidden";
      hiddenInput.name = "tag_ids";
      hiddenInput.value = tag.id;

      hiddenInputsContainer.appendChild(hiddenInput);
    });

    tagOptions.forEach(function (option) {
      const isSelected = selectedTags.has(option.dataset.tagId);
      const maxReached = selectedTags.size >= maxTags;

      option.classList.toggle("is-selected", isSelected);
      option.disabled = isSelected || (maxReached && !isSelected);
    });

    if (tagsToggle) {
      tagsToggle.textContent = selectedTags.size === 0
        ? "Add tags"
        : `${selectedTags.size} tag${selectedTags.size === 1 ? "" : "s"} selected`;
    }

    if (selectedTags.size === maxTags) {
      showTagHelper(`Maximum ${maxTags} tags selected.`, false);
    } else {
      showTagHelper(`Choose up to ${maxTags} tags.`, false);
    }
  }

  function showTagHelper(message, isWarning) {
    if (!helperText) return;

    helperText.textContent = message;
    helperText.classList.toggle("is-warning", Boolean(isWarning));
  }
}


function filterTagOptions(query, tagOptions) {
  const normalisedQuery = query.trim().toLowerCase();

  tagOptions.forEach(function (option) {
    const tagName = option.dataset.tagName.toLowerCase();
    const tagSlug = option.dataset.tagSlug.toLowerCase();

    const matches =
      normalisedQuery.length === 0 ||
      tagName.includes(normalisedQuery) ||
      tagSlug.includes(normalisedQuery);

    option.hidden = !matches;
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


// =========================
// Infinite scroll
// =========================

function initialiseForumInfiniteScroll() {
  const feed = document.querySelector("#forumFeed");
  const trigger = document.querySelector("#forumInfiniteScrollTrigger");
  const status = document.querySelector("#forumInfiniteScrollStatus");

  if (!feed || !trigger) {
    return;
  }

  let isLoading = false;

  async function loadMoreThreads() {
    if (isLoading || trigger.dataset.hasMore !== "true") {
      return;
    }

    isLoading = true;

    if (status) {
      status.hidden = false;
    }

    const params = new URLSearchParams(window.location.search);
    params.set("page", trigger.dataset.nextPage || "2");

    try {
      const response = await fetch(`/forum/api/threads?${params.toString()}`, {
        method: "GET",
        headers: {
          "X-Requested-With": "XMLHttpRequest"
        }
      });

      if (!response.ok) {
        throw new Error("Unable to load more forum threads.");
      }

      const data = await response.json();

      if (data.html && data.html.trim() !== "") {
        feed.insertAdjacentHTML("beforeend", data.html);
      }

      trigger.dataset.nextPage = data.next_page;
      trigger.dataset.hasMore = data.has_more ? "true" : "false";

      if (!data.has_more) {
        observer.unobserve(trigger);
      }
    } catch (error) {
      console.error("Unable to load more forum threads:", error);
    } finally {
      isLoading = false;

      if (status) {
        status.hidden = true;
      }
    }
  }

  const observer = new IntersectionObserver(
    function (entries) {
      const entry = entries[0];

      if (entry.isIntersecting) {
        loadMoreThreads();
      }
    },
    {
      root: null,
      rootMargin: "300px",
      threshold: 0
    }
  );

  if (trigger.dataset.hasMore === "true") {
    observer.observe(trigger);
  }
}