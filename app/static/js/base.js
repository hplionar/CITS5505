// =========================
// BASE LAYOUT INTERACTIONS
// =========================

document.addEventListener("DOMContentLoaded", function () {
  const appShell = document.querySelector(".app-shell");

  const sidebarToggle = document.querySelector("#sidebarToggle");
  const sidebarBackdrop = document.querySelector("#sidebarBackdrop");

  const profileToggle = document.querySelector("#profileToggle");
  const profileMenu = document.querySelector("#profileMenu");

  if (!appShell) return;

  // -------------------------
  // Helpers
  // -------------------------
  function isMobileLayout() {
    return window.innerWidth <= 900;
  }

  function setMobileSidebarOpen(isOpen) {
    appShell.classList.toggle("sidebar-open", isOpen);
    document.body.classList.toggle("sidebar-open", isOpen);

    if (sidebarToggle) {
      sidebarToggle.setAttribute("aria-expanded", String(isOpen));
    }
  }

  function closeMobileSidebar() {
    setMobileSidebarOpen(false);
  }

  // -------------------------
  // Sidebar collapse / mobile open
  // -------------------------
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", function (event) {
      event.stopPropagation();

      if (isMobileLayout()) {
        const isOpen = appShell.classList.contains("sidebar-open");
        setMobileSidebarOpen(!isOpen);
      } else {
        appShell.classList.toggle("sidebar-collapsed");

        const isExpanded = !appShell.classList.contains("sidebar-collapsed");
        sidebarToggle.setAttribute("aria-expanded", String(isExpanded));
      }
    });
  }

  if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener("click", function () {
      closeMobileSidebar();
    });
  }

  // -------------------------
  // Profile dropdown
  // -------------------------
  function openProfileMenu() {
    if (!profileToggle || !profileMenu) return;

    profileMenu.hidden = false;
    profileToggle.setAttribute("aria-expanded", "true");
  }

  function closeProfileMenu() {
    if (!profileToggle || !profileMenu) return;

    profileMenu.hidden = true;
    profileToggle.setAttribute("aria-expanded", "false");
  }

  function toggleProfileMenu() {
    if (!profileMenu) return;

    if (profileMenu.hidden) {
      openProfileMenu();
    } else {
      closeProfileMenu();
    }
  }

  if (profileToggle && profileMenu) {
    profileToggle.addEventListener("click", function (event) {
      event.stopPropagation();
      toggleProfileMenu();
    });

    profileMenu.addEventListener("click", function (event) {
      event.stopPropagation();
    });
  }

  // -------------------------
  // Close menus when clicking outside
  // -------------------------
  document.addEventListener("click", function (event) {
    const clickedInsideSidebar = event.target.closest(".sidebar");
    const clickedSidebarToggle = event.target.closest("#sidebarToggle");
    const clickedProfile = event.target.closest(".profile-dropdown");

    if (!clickedProfile) {
      closeProfileMenu();
    }

    if (
      isMobileLayout() &&
      !clickedInsideSidebar &&
      !clickedSidebarToggle
    ) {
      closeMobileSidebar();
    }
  });

  // -------------------------
  // Close menus with Escape
  // -------------------------
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeProfileMenu();
      closeMobileSidebar();
    }
  });

  // -------------------------
  // Reset mobile sidebar on resize
  // -------------------------
  window.addEventListener("resize", function () {
    if (!isMobileLayout()) {
      closeMobileSidebar();

      if (sidebarToggle) {
        const isExpanded = !appShell.classList.contains("sidebar-collapsed");
        sidebarToggle.setAttribute("aria-expanded", String(isExpanded));
      }
    }
  });
});