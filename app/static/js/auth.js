document.addEventListener("DOMContentLoaded", function () {
  // =========================
  // 1. Password visibility toggle
  // =========================
  const passwordToggles = document.querySelectorAll("[data-password-toggle]");

  passwordToggles.forEach(function (toggle) {
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

  // =========================
  // 2. Username availability check
  // =========================
  const usernameInput = document.querySelector("[data-check-url]");
  const usernameField = document.querySelector('[data-feedback-field="username"]');
  const usernameFeedback = document.querySelector("#username-feedback");
  const usernameStatus = document.querySelector("[data-username-status]");

  let latestUsernameRequest = 0;

  function clearUsernameFeedback() {
    if (!usernameField || !usernameFeedback || !usernameStatus) return;

    usernameField.classList.remove("is-valid", "is-invalid");
    usernameFeedback.classList.remove("is-success", "is-error");
    usernameFeedback.textContent = "";
    usernameStatus.textContent = "";
  }

  function setUsernameFeedback(isAvailable, message) {
    if (!usernameField || !usernameFeedback || !usernameStatus) return;

    usernameField.classList.remove("is-valid", "is-invalid");
    usernameFeedback.classList.remove("is-success", "is-error");

    if (isAvailable) {
      usernameField.classList.add("is-valid");
      usernameFeedback.classList.add("is-success");
      usernameStatus.textContent = "✓";
    } else {
      usernameField.classList.add("is-invalid");
      usernameFeedback.classList.add("is-error");
      usernameStatus.textContent = "!";
    }

    usernameFeedback.textContent = message;
  }

  async function checkUsernameAvailability() {
    if (!usernameInput) return;

    const username = usernameInput.value.trim();

    if (!username) {
      clearUsernameFeedback();
      return;
    }

    const requestId = ++latestUsernameRequest;
    const checkUrl = usernameInput.dataset.checkUrl;

    try {
      const response = await fetch(
        `${checkUrl}?username=${encodeURIComponent(username)}`
      );

      if (!response.ok) {
        setUsernameFeedback(false, "Could not check username. Please try again.");
        return;
      }

      const result = await response.json();

      if (requestId !== latestUsernameRequest) return;

      setUsernameFeedback(result.available, result.message);
    } catch (error) {
      setUsernameFeedback(false, "Could not check username. Please try again.");
    }
  }

  if (usernameInput && usernameField && usernameFeedback && usernameStatus) {
    // While typing, remove stale feedback.
    usernameInput.addEventListener("input", clearUsernameFeedback);

    // Only check when user leaves the username field.
    usernameInput.addEventListener("blur", checkUsernameAvailability);
  }
});

// =========================
// 3. Confirm password match check
// =========================
const passwordInput = document.querySelector("#register-password");
const confirmPasswordInput = document.querySelector("#confirm-password");
const confirmPasswordField = document.querySelector(
  '[data-feedback-field="confirm-password"]'
);
const confirmPasswordFeedback = document.querySelector(
  "#confirm-password-feedback"
);
const confirmPasswordStatus = document.querySelector(
  "[data-confirm-password-status]"
);

let confirmPasswordTimer = null;
const CONFIRM_PASSWORD_DELAY = 700;

function clearConfirmPasswordFeedback() {
  if (!confirmPasswordField || !confirmPasswordFeedback || !confirmPasswordStatus) {
    return;
  }

  confirmPasswordField.classList.remove("is-valid", "is-invalid");
  confirmPasswordFeedback.classList.remove("is-success", "is-error");
  confirmPasswordFeedback.textContent = "";
  confirmPasswordStatus.textContent = "";
}

function setConfirmPasswordFeedback(isMatch, message) {
  if (!confirmPasswordField || !confirmPasswordFeedback || !confirmPasswordStatus) {
    return;
  }

  confirmPasswordField.classList.remove("is-valid", "is-invalid");
  confirmPasswordFeedback.classList.remove("is-success", "is-error");

  if (isMatch) {
    confirmPasswordField.classList.add("is-valid");
    confirmPasswordFeedback.classList.add("is-success");
    confirmPasswordStatus.textContent = "✓";
  } else {
    confirmPasswordField.classList.add("is-invalid");
    confirmPasswordFeedback.classList.add("is-error");
    confirmPasswordStatus.textContent = "!";
  }

  confirmPasswordFeedback.textContent = message;
}

function checkConfirmPasswordMatch() {
  if (!passwordInput || !confirmPasswordInput) return;

  const password = passwordInput.value;
  const confirmPassword = confirmPasswordInput.value;

  if (!confirmPassword) {
    clearConfirmPasswordFeedback();
    return;
  }

  if (password === confirmPassword) {
    setConfirmPasswordFeedback(true, "Passwords match.");
  } else {
    setConfirmPasswordFeedback(false, "Passwords do not match.");
  }
}

function scheduleConfirmPasswordCheck() {
  clearConfirmPasswordFeedback();
  clearTimeout(confirmPasswordTimer);

  confirmPasswordTimer = setTimeout(function () {
    checkConfirmPasswordMatch();
  }, CONFIRM_PASSWORD_DELAY);
}

if (passwordInput && confirmPasswordInput) {
  // Validate after the user pauses typing in confirm password.
  confirmPasswordInput.addEventListener("input", scheduleConfirmPasswordCheck);

  // Validate immediately when the user leaves the confirm password field.
  confirmPasswordInput.addEventListener("blur", function () {
    clearTimeout(confirmPasswordTimer);
    checkConfirmPasswordMatch();
  });

  // If the original password changes, re-check only after a pause.
  passwordInput.addEventListener("input", function () {
    if (confirmPasswordInput.value) {
      scheduleConfirmPasswordCheck();
    }
  });
}