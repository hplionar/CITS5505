// =========================
// BASE LAYOUT INTERACTIONS
// =========================

document.addEventListener("DOMContentLoaded", function () {
  const appShell = document.querySelector(".app-shell");

  const sidebarToggle = document.querySelector("#sidebarToggle");
  const profileToggle = document.querySelector("#profileToggle");
  const profileMenu = document.querySelector("#profileMenu");

  if (!appShell) return;

  // -------------------------
  // Sidebar collapse / mobile open
  // -------------------------
  if (sidebarToggle) {
    sidebarToggle.addEventListener("click", function () {
      const isMobile = window.innerWidth <= 900;

      if (isMobile) {
        appShell.classList.toggle("sidebar-open");

        const isOpen = appShell.classList.contains("sidebar-open");
        sidebarToggle.setAttribute("aria-expanded", String(isOpen));
      } else {
        appShell.classList.toggle("sidebar-collapsed");

        const isExpanded = !appShell.classList.contains("sidebar-collapsed");
        sidebarToggle.setAttribute("aria-expanded", String(isExpanded));
      }
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

    if (!clickedInsideSidebar && !clickedSidebarToggle) {
      appShell.classList.remove("sidebar-open");
    }
  });

  // -------------------------
  // Close menus with Escape
  // -------------------------
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeProfileMenu();
      appShell.classList.remove("sidebar-open");
    }
  });

  // -------------------------
  // Reset mobile sidebar on resize
  // -------------------------
  window.addEventListener("resize", function () {
    if (window.innerWidth > 900) {
      appShell.classList.remove("sidebar-open");
    }
  });
});