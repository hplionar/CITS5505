const STORAGE_KEY = "studyhub_sessions";
const SAVED_KEY = "studyhub_saved_sessions";
const CURRENT_USER = "You";
const JSON_PATH = "../data/sessions.json";

const state = {
  mode: "all",
  sort: "soonest",
  query: "",
  day: "all",
  view: "all"
};

const modeTabs = document.getElementById("modeTabs");
const viewFilter = document.getElementById("viewFilter");
const sessionGrid = document.getElementById("sessionGrid");

const openCreateModal = document.getElementById("openCreateModal");
const closeCreateModal = document.getElementById("closeCreateModal");
const createPanel = document.getElementById("createPanel");
const modalBackdrop = document.getElementById("modalBackdrop");

const sessionForm = document.getElementById("sessionForm");
const resetFormBtn = document.getElementById("resetFormBtn");
const toastStack = document.getElementById("toastStack");

init();

async function init() {
  await seedDataFromJson();
  bindEvents();
  // renderSessions();
}

async function seedDataFromJson() {
  const existingSessions = localStorage.getItem(STORAGE_KEY);
  const existingSaved = localStorage.getItem(SAVED_KEY);

  if (!existingSaved) {
    localStorage.setItem(SAVED_KEY, JSON.stringify([]));
  }

  if (existingSessions) {
    return;
  }

  try {
    const response = await fetch(JSON_PATH);

    if (!response.ok) {
      throw new Error(`Failed to load JSON: ${response.status}`);
    }

    const sessions = await response.json();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
  } catch (error) {
    console.error("Unable to load sessions.json", error);
    localStorage.setItem(STORAGE_KEY, JSON.stringify([]));
    // summaryText.textContent = "Could not load initial sessions data.";
  }
}

function bindEvents() {
  // modeTabs.addEventListener("click", handleModeChange);
  openCreateModal.addEventListener("click", openPanel);
  closeCreateModal.addEventListener("click", closePanel);
  modalBackdrop.addEventListener("click", closePanel);

  sessionGrid.addEventListener("click", (event) => {
    console.log("Grid click:", event.target);
    const joinBtn = event.target.closest("[data-action='join']");
    const leaveBtn = event.target.closest("[data-action='leave']");
    const saveBtn = event.target.closest("[data-action='save']");

    if (joinBtn) handleJoin(joinBtn.dataset.id);
    if (leaveBtn) handleLeave(leaveBtn.dataset.id);
    if (saveBtn) handleSave(saveBtn.dataset.id);

    document.querySelectorAll(".session-card").forEach(card => {
      card.addEventListener("click", function () {
        window.location.href = this.dataset.url;
      });
    });
  });

}

function handleModeChange(event) {
  console.log("bindEvents")
  const button = event.target.closest(".tab-btn");
  if (!button) return;

  document.querySelectorAll(".tab-btn").forEach((tab) => tab.classList.remove("active"));
  button.classList.add("active");
  state.mode = button.dataset.mode;
  renderSessions();
}

function handleSortChange(event) {
  state.sort = event.target.value;
  renderSessions();
}

function handleSearchChange(event) {
  state.query = event.target.value.trim().toLowerCase();
  renderSessions();
}

function handleDayChange(event) {
  state.day = event.target.value;
  renderSessions();
}

function handleViewChange(event) {
  state.view = event.target.value;
  renderSessions();
}

function openPanel() {
  createPanel.classList.add("open");
  modalBackdrop.classList.add("show");
  createPanel.setAttribute("aria-hidden", "false");
}

function closePanel() {
  createPanel.classList.remove("open");
  modalBackdrop.classList.remove("show");
  createPanel.setAttribute("aria-hidden", "true");
}

function getSessions() {
  return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
}

function saveSessions(sessions) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
}

function getSavedIds() {
  return JSON.parse(localStorage.getItem(SAVED_KEY)) || [];
}

function saveSavedIds(ids) {
  localStorage.setItem(SAVED_KEY, JSON.stringify(ids));
}

function handleJoin(sessionId) {
  const sessions = getSessions();
  const session = sessions.find((item) => item.id === sessionId);

  if (!session) return;

  if (session.joinedBy.includes(CURRENT_USER)) {
    showToast("You have already joined this session.");
    return;
  }

  if (session.joined >= session.capacity) {
    showToast("This session is already full.");
    return;
  }

  session.joined += 1;
  session.joinedBy.push(CURRENT_USER);

  saveSessions(sessions);
  showToast("You joined this session.");
  renderSessions();
}

function handleLeave(sessionId) {
  const sessions = getSessions();
  const session = sessions.find((item) => item.id === sessionId);

  if (!session) return;
  if (!session.joinedBy.includes(CURRENT_USER)) return;

  session.joinedBy = session.joinedBy.filter((name) => name !== CURRENT_USER);
  session.joined = Math.max(0, session.joined - 1);

  saveSessions(sessions);
  showToast("You left this session.");
  renderSessions();
}

function handleSave(sessionId) {
  const savedIds = getSavedIds();
  const alreadySaved = savedIds.includes(sessionId);

  const updatedSavedIds = alreadySaved
    ? savedIds.filter((id) => id !== sessionId)
    : [...savedIds, sessionId];

  saveSavedIds(updatedSavedIds);
  showToast(alreadySaved ? "Removed from saved sessions." : "Saved for later.");
  renderSessions();
}

function handleCreateSession(event) {
  event.preventDefault();
  clearErrors();

  const formData = new FormData(sessionForm);
  const payload = Object.fromEntries(formData.entries());
  const errors = validateForm(payload);

  if (Object.keys(errors).length > 0) {
    showErrors(errors);
    return;
  }

  const newSession = {
    id: `session-${Date.now()}`,
    unitCode: payload.unitCode.trim().toUpperCase(),
    topic: payload.topic.trim(),
    description: payload.description.trim(),
    hostName: payload.hostName.trim(),
    day: payload.day,
    time: payload.time.trim(),
    sortRank: 0,
    mode: payload.mode,
    joined: 1,
    capacity: Number(payload.capacity),
    joinedBy: [CURRENT_USER],
    createdBy: CURRENT_USER,
    createdAt: Date.now()
  };

  const sessions = getSessions();
  sessions.unshift(newSession);
  saveSessions(sessions);

  sessionForm.reset();
  closePanel();
  state.view = "all";
  viewFilter.value = "all";

  showToast("Study session created successfully.");
  renderSessions();
}

function validateForm(payload) {
  const errors = {};

  if (!payload.unitCode.trim()) {
    errors.unitCode = "Please enter a unit or category.";
  }

  if (!payload.topic.trim()) {
    errors.topic = "Please enter a session title.";
  }

  if (!payload.description.trim()) {
    errors.description = "Please enter a description.";
  }

  if (!payload.hostName.trim()) {
    errors.hostName = "Please enter a host name.";
  }

  if (!payload.day) {
    errors.day = "Please select a day.";
  }

  if (!payload.time.trim()) {
    errors.time = "Please enter a time.";
  }

  if (!payload.mode) {
    errors.mode = "Please select a mode.";
  }

  const capacity = Number(payload.capacity);
  if (!payload.capacity || Number.isNaN(capacity) || capacity < 2) {
    errors.capacity = "Capacity must be at least 2.";
  }

  return errors;
}

function showErrors(errors) {
  Object.entries(errors).forEach(([field, message]) => {
    const errorEl = document.querySelector(`[data-error-for="${field}"]`);
    if (errorEl) {
      errorEl.textContent = message;
    }
  });
}

function clearErrors() {
  document.querySelectorAll(".error-text").forEach((el) => {
    el.textContent = "";
  });
}

function renderSessions() {
  const sessions = getSessions();
  const savedIds = getSavedIds();

  let filteredSessions = sessions.filter((session) => {
    const modeMatch = state.mode === "all" || session.mode === state.mode;
    const dayMatch = state.day === "all" || session.day === state.day;

    const searchText = `${session.unitCode} ${session.topic} ${session.description}`.toLowerCase();
    const queryMatch = !state.query || searchText.includes(state.query);

    let viewMatch = true;
    if (state.view === "joined") {
      viewMatch = session.joinedBy.includes(CURRENT_USER);
    } else if (state.view === "saved") {
      viewMatch = savedIds.includes(session.id);
    } else if (state.view === "hosted") {
      viewMatch = session.createdBy === CURRENT_USER;
    }

    return modeMatch && dayMatch && queryMatch && viewMatch;
  });

  console.log("Filtered sessions:", sessions);
  filteredSessions = sortSessions(filteredSessions);
  
  if (filteredSessions.length === 0) {
    sessionGrid.innerHTML = `
      <div class="empty-state">
        <h3>No matching sessions found</h3>
        <p>Try changing the filters or create a new study session.</p>
      </div>
    `;
    return;
  }

  sessionGrid.innerHTML = filteredSessions
    .map((session) => createSessionCard(session, savedIds))
    .join("");
}

function sortSessions(sessions) {
  const sorted = [...sessions];

  if (state.sort === "popular") {
    sorted.sort((a, b) => (b.joined / b.capacity) - (a.joined / a.capacity));
  } else if (state.sort === "newest") {
    sorted.sort((a, b) => b.createdAt - a.createdAt);
  } else {
    sorted.sort((a, b) => a.sortRank - b.sortRank || b.createdAt - a.createdAt);
  }

  return sorted;
}

function buildSummaryText() {
  const parts = [];

  if (state.mode !== "all") {
    parts.push(`mode: ${formatMode(state.mode)}`);
  }

  if (state.day !== "all") {
    parts.push(`day: ${state.day}`);
  }

  if (state.view !== "all") {
    parts.push(`view: ${state.view}`);
  }

  if (state.query) {
    parts.push(`search: "${state.query}"`);
  }

  return parts.length ? `Filtered by ${parts.join(" · ")}` : "Showing all available study sessions";
}

function createSessionCard(session, savedIds) {
  const isJoined = session.joinedBy.includes(CURRENT_USER);
  const isSaved = savedIds.includes(session.id);
  const isFull = session.joined >= session.capacity;

  return `
    <article class="session-card" data-url="${url_for("session_detail", session_id=session.id)}">
      <div>
        <p class="session-card__tag">${escapeHtml(session.unitCode)}</p>

        ${isJoined ? `<div class="session-card__badge session-card__badge--joined">✓ Joined by you</div>` : ""}
        ${!isJoined && isFull ? `<div class="session-card__badge session-card__badge--full">Session full</div>` : ""}

        <h3 class="session-card__title">${escapeHtml(session.topic)}</h3>
        <p class="session-card__desc">${escapeHtml(session.description)}</p>

        <div class="meta-grid">
          <div class="meta-item"><strong>Host:</strong> ${escapeHtml(session.hostName)}</div>
          <div class="meta-item"><strong>Mode:</strong> ${formatMode(session.mode)}</div>
          <div class="meta-item"><strong>Time:</strong> ${escapeHtml(session.time)}</div>
          <div class="meta-item"><strong>Joined:</strong> ${session.joined} / ${session.capacity}</div>
        </div>
      </div>

      <div class="card-actions">
        ${
          isJoined
            ? `<button class="btn btn--leave" data-action="leave" data-id="${session.id}" type="button">Leave Session</button>`
            : `<button class="btn btn--dark" data-action="join" data-id="${session.id}" type="button" ${isFull ? "disabled" : ""}>
                ${isFull ? "Session Full" : "Join Session"}
              </button>`
        }

        <button class="btn btn--light btn--save ${isSaved ? "saved" : ""}" data-action="save" data-id="${session.id}" type="button">
          ${isSaved ? "Saved" : "Save"}
        </button>
      </div>
    </article>
  `;
}

function formatMode(mode) {
  if (mode === "in-person") return "In person";
  if (mode === "online") return "Online";
  if (mode === "hybrid") return "Hybrid";
  return mode;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function showToast(message) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  toastStack.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 2600);
}
