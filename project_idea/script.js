const appLayout = document.getElementById('appLayout');
const sidebarToggle = document.getElementById('sidebarToggle');
const avatarBtn = document.getElementById('avatarBtn');
const userDropdown = document.getElementById('userDropdown');

if (sidebarToggle && appLayout) {
  sidebarToggle.addEventListener('click', () => {
    appLayout.classList.toggle('sidebar-collapsed');
  });
}

if (avatarBtn && userDropdown) {
  avatarBtn.addEventListener('click', (event) => {
    event.stopPropagation();
    userDropdown.classList.toggle('open');
  });

  document.addEventListener('click', (event) => {
    const clickedInsideMenu = userDropdown.contains(event.target);
    const clickedAvatar = avatarBtn.contains(event.target);

    if (!clickedInsideMenu && !clickedAvatar) {
      userDropdown.classList.remove('open');
    }
  });
}