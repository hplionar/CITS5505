document.addEventListener("DOMContentLoaded", function () {
  const storageKey = "cshub.readAnnouncements";
  const openButtons = document.querySelectorAll("[data-announcement-open]");
  const closeButtons = document.querySelectorAll("[data-announcement-close]");
  const modals = document.querySelectorAll("[data-announcement-modal]");

  function getReadAnnouncements() {
    try {
      return JSON.parse(localStorage.getItem(storageKey)) || [];
    } catch (error) {
      return [];
    }
  }

  function saveReadAnnouncements(readAnnouncements) {
    localStorage.setItem(storageKey, JSON.stringify(readAnnouncements));
  }

  function markAnnouncementAsRead(button) {
    const announcementId = button.dataset.announcementId;
    if (!announcementId) return;

    const readAnnouncements = getReadAnnouncements();
    if (!readAnnouncements.includes(announcementId)) {
      readAnnouncements.push(announcementId);
      saveReadAnnouncements(readAnnouncements);
    }

    button.classList.add("is-read");
    button.setAttribute("aria-label", "Read announcement: " + button.innerText.trim());
  }

  function applyReadState() {
    const readAnnouncements = getReadAnnouncements();

    openButtons.forEach(function (button) {
      if (readAnnouncements.includes(button.dataset.announcementId)) {
        button.classList.add("is-read");
      }
    });
  }

  function closeAllModals() {
    modals.forEach(function (modal) {
      modal.hidden = true;
    });
  }

  openButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      const modal = document.getElementById(button.dataset.announcementOpen);
      if (!modal) return;

      closeAllModals();
      modal.hidden = false;
      markAnnouncementAsRead(button);

      const closeButton = modal.querySelector("[data-announcement-close]");
      if (closeButton) closeButton.focus();
    });
  });

  closeButtons.forEach(function (button) {
    button.addEventListener("click", closeAllModals);
  });

  modals.forEach(function (modal) {
    modal.addEventListener("click", function (event) {
      if (event.target === modal) {
        closeAllModals();
      }
    });
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeAllModals();
    }
  });

  applyReadState();
});
