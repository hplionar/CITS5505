// =========================
// FORUM EXPLORE FEED
// =========================

document.addEventListener("DOMContentLoaded", function () {
  const feed = document.querySelector("#forumFeed");
  const sentinel = document.querySelector("#forumFeedSentinel");
  const loading = document.querySelector("#forumLoading");
  const endMessage = document.querySelector("#forumEndMessage");

  if (!feed || !sentinel) return;

  const PAGE_SIZE = 20;

  let currentPage = 0;
  let currentSort = "recent";
  let currentView = "explore";
  let isLoading = false;
  let hasMore = true;

  // Temporary mock data for UI development.
  // Later, replace loadThreads() with fetch() from Flask.
  const mockThreads = buildMockThreads(100);

  // -------------------------
  // Dropdown behaviour
  // -------------------------
  const dropdowns = document.querySelectorAll("[data-dropdown]");

  dropdowns.forEach(function (dropdown) {
    const toggle = dropdown.querySelector("[data-dropdown-toggle]");
    const menu = dropdown.querySelector("[data-dropdown-menu]");

    if (!toggle || !menu) return;

    toggle.addEventListener("click", function (event) {
      event.stopPropagation();

      const isOpen = !menu.hidden;
      closeAllDropdowns();

      menu.hidden = isOpen;
      toggle.setAttribute("aria-expanded", String(!isOpen));
    });

    menu.addEventListener("click", function (event) {
      event.stopPropagation();
    });
  });

  document.addEventListener("click", function () {
    closeAllDropdowns();
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeAllDropdowns();
    }
  });

  function closeAllDropdowns() {
    dropdowns.forEach(function (dropdown) {
      const toggle = dropdown.querySelector("[data-dropdown-toggle]");
      const menu = dropdown.querySelector("[data-dropdown-menu]");

      if (!toggle || !menu) return;

      menu.hidden = true;
      toggle.setAttribute("aria-expanded", "false");
    });
  }

  // -------------------------
  // View selection
  // -------------------------
  document.querySelectorAll("[data-view-option]").forEach(function (button) {
    button.addEventListener("click", function () {
      const nextView = button.dataset.viewOption;

      document.querySelectorAll("[data-view-option]").forEach(function (item) {
        item.classList.remove("is-active");
      });

      button.classList.add("is-active");

      const label = document.querySelector("[data-view-label]");
      if (label) {
        label.textContent = nextView === "categories" ? "Categories" : "Explore";
      }

      currentView = nextView;
      closeAllDropdowns();

      if (currentView === "categories") {
        showCategoryPlaceholder();
      } else {
        resetAndLoad();
      }
    });
  });

  function showCategoryPlaceholder() {
    feed.innerHTML = `
      <div class="forum-placeholder-card">
        <p class="forum-placeholder-title">Category view will be added next.</p>
        <p class="forum-placeholder-text">
          For now, this screen focuses on the compact Explore feed.
        </p>
      </div>
    `;

    hasMore = false;

    if (loading) loading.hidden = true;
    if (endMessage) endMessage.hidden = true;
  }

  // -------------------------
  // Sort selection
  // -------------------------
  document.querySelectorAll("[data-sort-option]").forEach(function (button) {
    button.addEventListener("click", function () {
      const nextSort = button.dataset.sortOption;
      const labelText =
        button.querySelector("strong")?.textContent || "Recently Active";

      document.querySelectorAll("[data-sort-option]").forEach(function (item) {
        item.classList.remove("is-active");
      });

      button.classList.add("is-active");

      const label = document.querySelector("[data-sort-label]");
      if (label) {
        label.textContent = labelText;
      }

      currentSort = nextSort;
      currentView = "explore";

      const viewLabel = document.querySelector("[data-view-label]");
      if (viewLabel) {
        viewLabel.textContent = "Explore";
      }

      document.querySelectorAll("[data-view-option]").forEach(function (item) {
        item.classList.toggle(
          "is-active",
          item.dataset.viewOption === "explore"
        );
      });

      closeAllDropdowns();
      resetAndLoad();
    });
  });

  // -------------------------
  // Thread card interactions
  // -------------------------
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

  function toggleThreadLike(button) {
    const countElement = button.querySelector("[data-like-count]");
    const icon = button.querySelector("i");

    const isLiked = button.classList.toggle("is-liked");
    const currentCount = Number(countElement?.textContent || 0);
    const nextCount = isLiked ? currentCount + 1 : Math.max(0, currentCount - 1);

    if (countElement) {
      countElement.textContent = String(nextCount);
    }

    if (icon) {
      icon.className = isLiked
        ? "bi bi-hand-thumbs-up-fill"
        : "bi bi-hand-thumbs-up";
    }

    button.setAttribute("aria-pressed", String(isLiked));
  }

  function toggleThreadSave(button) {
    const icon = button.querySelector("i");
    const isSaved = button.classList.toggle("is-saved");

    if (icon) {
      icon.className = isSaved ? "bi bi-bookmark-fill" : "bi bi-bookmark";
    }

    button.setAttribute("aria-pressed", String(isSaved));
    button.setAttribute("aria-label", isSaved ? "Unsave thread" : "Save thread");
  }

  // -------------------------
  // Infinite loading
  // -------------------------
  const observer = new IntersectionObserver(
    function (entries) {
      const entry = entries[0];

      if (
        entry.isIntersecting &&
        hasMore &&
        !isLoading &&
        currentView === "explore"
      ) {
        loadNextPage();
      }
    },
    {
      root: null,
      rootMargin: "650px 0px",
      threshold: 0
    }
  );

  observer.observe(sentinel);

  function resetAndLoad() {
    currentPage = 0;
    hasMore = true;
    isLoading = false;

    feed.innerHTML = "";

    if (endMessage) endMessage.hidden = true;

    loadNextPage();
  }

  async function loadNextPage() {
    if (isLoading || !hasMore) return;

    isLoading = true;
    if (loading) loading.hidden = false;

    try {
      const threads = await loadThreads({
        page: currentPage + 1,
        pageSize: PAGE_SIZE,
        sort: currentSort
      });

      if (threads.length < PAGE_SIZE) {
        hasMore = false;
      }

      currentPage += 1;
      renderThreads(threads);

      if (!hasMore && endMessage) {
        endMessage.hidden = false;
      }
    } catch (error) {
      console.error("Failed to load forum threads:", error);
      renderErrorMessage();
      hasMore = false;
    } finally {
      isLoading = false;
      if (loading) loading.hidden = true;
    }
  }

  async function loadThreads({ page, pageSize, sort }) {
    // Later Flask API version:
    //
    // const response = await fetch(
    //   `/forum/api/threads?sort=${encodeURIComponent(sort)}&page=${page}&page_size=${pageSize}`
    // );
    //
    // if (!response.ok) throw new Error("Failed to fetch threads");
    // const data = await response.json();
    // hasMore = data.has_more;
    // return data.threads;

    await wait(250);

    const sortedThreads = getSortedThreads(mockThreads, sort);

    const start = (page - 1) * pageSize;
    const end = start + pageSize;

    return sortedThreads.slice(start, end);
  }

  function renderThreads(threads) {
    const fragment = document.createDocumentFragment();

    threads.forEach(function (thread) {
      const article = document.createElement("article");
      article.className = "thread-card";
      article.dataset.threadId = String(thread.id);

      article.innerHTML = `
        <div class="thread-content">
          <div class="thread-meta">
            ${
              thread.isPinned
                ? `<span class="thread-pinned">
                     <i class="bi bi-pin-angle-fill" aria-hidden="true"></i>
                     Pinned
                   </span>
                   <span class="thread-dot">·</span>`
                : ""
            }

            <span class="thread-category">${escapeHTML(thread.category)}</span>
            <span class="thread-dot">·</span>
            <span class="thread-author">Posted by ${escapeHTML(thread.author)}</span>
            <span class="thread-dot">·</span>
            <span>${escapeHTML(thread.timeAgo)}</span>
          </div>

          <a href="${escapeHTML(thread.url)}" class="thread-title">
            ${escapeHTML(thread.title)}
          </a>

          <div class="thread-footer">
            <div class="thread-actions">
              <button
                class="thread-action thread-expand-button"
                type="button"
                aria-label="Expand thread"
                aria-expanded="false"
                data-expand-thread
              >
                <i class="bi bi-arrows-angle-expand" aria-hidden="true"></i>
              </button>

              <button
                class="thread-action thread-like-button"
                type="button"
                aria-label="Like thread"
                aria-pressed="false"
                data-like-thread
              >
                <i class="bi bi-hand-thumbs-up" aria-hidden="true"></i>
                <span data-like-count>${thread.likeCount}</span>
              </button>

              <a href="${escapeHTML(thread.url)}#comments" class="thread-action thread-comments-link">
                <span>${thread.commentCount} comments</span>
              </a>

              <button
                class="thread-action thread-save-button"
                type="button"
                aria-label="Save thread"
                aria-pressed="false"
                data-save-thread
              >
                <i class="bi bi-bookmark" aria-hidden="true"></i>
              </button>
            </div>

            <div class="thread-tags">
              ${thread.tags
                .map(function (tag) {
                  return `<span class="thread-tag">#${escapeHTML(tag)}</span>`;
                })
                .join("")}
            </div>
          </div>

          <p class="thread-body" hidden>
            ${formatText(thread.body)}
          </p>
        </div>
      `;

      fragment.appendChild(article);
    });

    feed.appendChild(fragment);
  }

  function renderErrorMessage() {
    const errorCard = document.createElement("div");
    errorCard.className = "forum-placeholder-card";

    errorCard.innerHTML = `
      <p class="forum-placeholder-title">Unable to load more discussions</p>
      <p class="forum-placeholder-text">Please refresh the page and try again.</p>
    `;

    feed.appendChild(errorCard);
  }

  function getSortedThreads(threads, sort) {
    const copy = [...threads];

    let sorted;

    if (sort === "popular") {
      sorted = copy.sort(function (a, b) {
        const scoreA = a.likeCount * 2 + a.commentCount;
        const scoreB = b.likeCount * 2 + b.commentCount;
        return scoreB - scoreA;
      });
    } else if (sort === "new") {
      sorted = copy.sort(function (a, b) {
        return b.createdAt - a.createdAt;
      });
    } else {
      sorted = copy.sort(function (a, b) {
        return b.lastActivityAt - a.lastActivityAt;
      });
    }

    return sorted.sort(function (a, b) {
      if (a.isPinned && !b.isPinned) return -1;
      if (!a.isPinned && b.isPinned) return 1;
      return 0;
    });
  }

  function buildMockThreads(count) {
    const authors = [
      "Hans",
      "Alice",
      "Daniel",
      "Maya",
      "Kevin",
      "Sarah",
      "Tutor Alex"
    ];

    const dummyCategories = [
      "General",
      "AI & Data Science",
      "Software Engineering",
      "Computer Science",
      "Courses & Study Help"
    ];

    const featuredThreads = [
      {
        type: "discussion",
        category: "General",
        title: "How are you preparing for the CITS5508 Machine Learning exam?",
        body:
          "How are you preparing for the CITS5508 Machine Learning exam since there’s no cheat sheet allowed? Any tips appreciated.\n\nInspired by a real r/UWA thread: https://www.reddit.com/r/uwa/comments/1t1jad6/cits_5508_machine_learning/",
        tags: ["study-tips", "cits5508", "exam-prep"]
      },
      {
        type: "question",
        category: "Software Engineering",
        title: "I still do not really understand Model-View-Controller",
        body:
          "I keep seeing Model-View-Controller explained as Model for data, View for UI, and Controller for application logic. But in our actual Flask project, I am not sure how to map that idea properly. For example, are the SQLAlchemy classes in models.py the Model? Are Jinja templates the View? And are the route functions the Controller? I think I understand the words, but not how the pieces connect in a real codebase.",
        tags: ["mvc", "flask", "web-development"]
      },
      {
        type: "question",
        category: "AI & Data Science",
        title: "I still do not really understand the idea behind PCA",
        body:
          "I understand that PCA is used for dimensionality reduction, but I am still confused about the intuition. When we say PCA finds directions of maximum variance, does that mean it is finding the most important features? How should I think about principal components in a simple way, especially when the original dataset has many columns?",
        tags: ["machine-learning", "pca", "intuition"]
      }
    ];

    const threads = [];
    const now = Date.now();

    for (let i = 1; i <= count; i += 1) {
      let threadData;

      if (i <= featuredThreads.length) {
        threadData = featuredThreads[i - 1];
      } else {
        const category = dummyCategories[i % dummyCategories.length];

        threadData = {
          type: "discussion",
          category: category,
          title: `Dummy forum thread #${i}`,
          body:
            "This is dummy body content for UI testing. Later, this will be replaced by real forum posts from the database. For now, it helps us check spacing, scrolling, sorting, expansion, and card density.",
          tags: ["dummy", "scroll-test"]
        };
      }

      const createdAt = now - i * 1000 * 60 * 60;
      const lastActivityAt = now - i * 1000 * 60;

      threads.push({
        id: i,
        type: threadData.type,
        title: threadData.title,
        body: threadData.body,
        category: threadData.category,
        author: authors[(i - 1) % authors.length],
        tags: threadData.tags,
        likeCount: i <= 3 ? i * 8 + 4 : (i * 7) % 96,
        commentCount: i <= 3 ? i * 3 + 2 : (i * 3) % 38,
        isPinned: i === 1,
        createdAt: createdAt,
        lastActivityAt: lastActivityAt,
        timeAgo: makeTimeAgo(i),
        url: `/forum/thread/${i}`
      });
    }

    return threads;
  }

  function makeTimeAgo(index) {
    if (index < 2) return "10m ago";
    if (index < 6) return `${index}h ago`;
    if (index < 20) return `${Math.floor(index / 2)}d ago`;

    return `${Math.floor(index / 7)}w ago`;
  }

  function wait(ms) {
    return new Promise(function (resolve) {
      window.setTimeout(resolve, ms);
    });
  }

  function formatText(value) {
    const escapedText = escapeHTML(value).replaceAll("\n", "<br>");

    return escapedText.replace(
      /(https?:\/\/[^\s<]+)/g,
      '<a class="thread-body-link" href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
    );
  }

  function escapeHTML(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  // Initial load
  resetAndLoad();
});