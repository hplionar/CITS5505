document.addEventListener("DOMContentLoaded", function () {
  const toggles = document.querySelectorAll("[data-password-toggle]");

  toggles.forEach(function (toggle) {
    const inputId = toggle.getAttribute("aria-controls");
    const passwordInput = document.getElementById(inputId);

    if (!passwordInput) return;

    toggle.addEventListener("click", function () {
      const isHidden = passwordInput.type === "password";

      passwordInput.type = isHidden ? "text" : "password";
      toggle.setAttribute(
        "aria-label",
        isHidden ? "Hide password" : "Show password"
      );

      passwordInput.focus();
    });
  });
});