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
  // 2. Generic feedback helpers
  // =========================
  function clearFieldFeedback(field, feedback, status) {
    if (!field || !feedback || !status) return;

    field.classList.remove("is-valid", "is-invalid");
    feedback.classList.remove("is-success", "is-error");
    feedback.textContent = "";
    status.textContent = "";
  }

  function setFieldFeedback(field, feedback, status, isValid, message) {
    if (!field || !feedback || !status) return;

    field.classList.remove("is-valid", "is-invalid");
    feedback.classList.remove("is-success", "is-error");

    if (isValid) {
      field.classList.add("is-valid");
      feedback.classList.add("is-success");
      status.textContent = "OK";
    } else {
      field.classList.add("is-invalid");
      feedback.classList.add("is-error");
      status.textContent = "!";
    }

    feedback.textContent = message;
  }

  // =========================
  // 3. Username availability check
  // =========================
  const usernameInput = document.querySelector("#register-username");
  const usernameField = document.querySelector('[data-feedback-field="username"]');
  const usernameFeedback = document.querySelector("#username-feedback");
  const usernameStatus = document.querySelector("[data-username-status]");

  let latestUsernameRequest = 0;

  async function checkUsernameAvailability() {
    if (!usernameInput) return;

    const username = usernameInput.value.trim();

    if (!username) {
      clearFieldFeedback(usernameField, usernameFeedback, usernameStatus);
      return;
    }

    const requestId = ++latestUsernameRequest;
    const checkUrl = usernameInput.dataset.checkUrl;

    try {
      const response = await fetch(
        `${checkUrl}?username=${encodeURIComponent(username)}`
      );

      if (!response.ok) {
        setFieldFeedback(
          usernameField,
          usernameFeedback,
          usernameStatus,
          false,
          "Could not check username. Please try again."
        );
        return;
      }

      const result = await response.json();

      if (requestId !== latestUsernameRequest) return;

      if (result.available) {
        // Available username: green check only, no success text.
        setFieldFeedback(usernameField, usernameFeedback, usernameStatus, true, "");
      } else {
        setFieldFeedback(
          usernameField,
          usernameFeedback,
          usernameStatus,
          false,
          result.message
        );
      }
    } catch (error) {
      setFieldFeedback(
        usernameField,
        usernameFeedback,
        usernameStatus,
        false,
        "Could not check username. Please try again."
      );
    }
  }

  if (usernameInput && usernameField && usernameFeedback && usernameStatus) {
    usernameInput.addEventListener("input", function () {
      clearFieldFeedback(usernameField, usernameFeedback, usernameStatus);
    });

    usernameInput.addEventListener("blur", checkUsernameAvailability);
  }

  // =========================
  // 4. Email availability check
  // =========================
  const emailInput = document.querySelector("#register-email");
  const emailField = document.querySelector('[data-feedback-field="email"]');
  const emailFeedback = document.querySelector("#email-feedback");
  const emailStatus = document.querySelector("[data-email-status]");

  let latestEmailRequest = 0;

  async function checkEmailAvailability() {
    if (!emailInput) return;

    const email = emailInput.value.trim();

    if (!email) {
      clearFieldFeedback(emailField, emailFeedback, emailStatus);
      return;
    }

    // Let native HTML validation handle invalid email format.
    if (!emailInput.checkValidity()) {
      clearFieldFeedback(emailField, emailFeedback, emailStatus);
      return;
    }

    const requestId = ++latestEmailRequest;
    const checkUrl = emailInput.dataset.checkUrl;

    try {
      const response = await fetch(
        `${checkUrl}?email=${encodeURIComponent(email)}`
      );

      if (!response.ok) {
        setFieldFeedback(
          emailField,
          emailFeedback,
          emailStatus,
          false,
          "Could not check email. Please try again."
        );
        return;
      }

      const result = await response.json();

      if (requestId !== latestEmailRequest) return;

      if (result.available) {
        // Available email: green check only, no success text.
        setFieldFeedback(emailField, emailFeedback, emailStatus, true, "");
      } else {
        setFieldFeedback(
          emailField,
          emailFeedback,
          emailStatus,
          false,
          result.message
        );
      }
    } catch (error) {
      setFieldFeedback(
        emailField,
        emailFeedback,
        emailStatus,
        false,
        "Could not check email. Please try again."
      );
    }
  }

  if (emailInput && emailField && emailFeedback && emailStatus) {
    emailInput.addEventListener("input", function () {
      clearFieldFeedback(emailField, emailFeedback, emailStatus);
    });

    emailInput.addEventListener("blur", checkEmailAvailability);
  }

  // =========================
  // 5. Password strength check
  // =========================
  const passwordInput = document.querySelector("#register-password");
  const passwordField = document.querySelector('[data-feedback-field="password"]');
  const passwordFeedback = document.querySelector("#password-feedback");
  const passwordStatus = document.querySelector("[data-password-status]");

  let passwordTimer = null;
  const PASSWORD_DELAY = 700;

  function validatePasswordStrength() {
    if (!passwordInput) return;

    const password = passwordInput.value;
    const hasMinimumLength = password.length >= 8;
    const hasLetter = /[A-Za-z]/.test(password);
    const hasNumber = /\d/.test(password);

    if (!password) {
      clearFieldFeedback(passwordField, passwordFeedback, passwordStatus);
      return;
    }

    if (!hasMinimumLength) {
      setFieldFeedback(
        passwordField,
        passwordFeedback,
        passwordStatus,
        false,
        "Password must be at least 8 characters."
      );
      return;
    }

    if (!hasLetter || !hasNumber) {
      setFieldFeedback(
        passwordField,
        passwordFeedback,
        passwordStatus,
        false,
        "Use at least one letter and one number."
      );
      return;
    }

    // Valid password: no green check, no success message.
    clearFieldFeedback(passwordField, passwordFeedback, passwordStatus);
  }

  function schedulePasswordStrengthCheck() {
    clearFieldFeedback(passwordField, passwordFeedback, passwordStatus);
    clearTimeout(passwordTimer);

    passwordTimer = setTimeout(function () {
      validatePasswordStrength();
    }, PASSWORD_DELAY);
  }

  if (passwordInput && passwordField && passwordFeedback && passwordStatus) {
    passwordInput.addEventListener("input", schedulePasswordStrengthCheck);

    passwordInput.addEventListener("blur", function () {
      clearTimeout(passwordTimer);
      validatePasswordStrength();
    });
  }

  // =========================
  // 6. Confirm password match check
  // =========================
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

  function validateConfirmPassword() {
    if (!passwordInput || !confirmPasswordInput) return;

    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;

    if (!confirmPassword) {
      clearFieldFeedback(
        confirmPasswordField,
        confirmPasswordFeedback,
        confirmPasswordStatus
      );
      return;
    }

    if (password !== confirmPassword) {
      setFieldFeedback(
        confirmPasswordField,
        confirmPasswordFeedback,
        confirmPasswordStatus,
        false,
        "Passwords do not match."
      );
      return;
    }

    // Matching password: no green check, no success message.
    clearFieldFeedback(
      confirmPasswordField,
      confirmPasswordFeedback,
      confirmPasswordStatus
    );
  }

  function scheduleConfirmPasswordCheck() {
    clearFieldFeedback(
      confirmPasswordField,
      confirmPasswordFeedback,
      confirmPasswordStatus
    );

    clearTimeout(confirmPasswordTimer);

    confirmPasswordTimer = setTimeout(function () {
      validateConfirmPassword();
    }, CONFIRM_PASSWORD_DELAY);
  }

  if (
    passwordInput &&
    confirmPasswordInput &&
    confirmPasswordField &&
    confirmPasswordFeedback &&
    confirmPasswordStatus
  ) {
    confirmPasswordInput.addEventListener("input", scheduleConfirmPasswordCheck);

    confirmPasswordInput.addEventListener("blur", function () {
      clearTimeout(confirmPasswordTimer);
      validateConfirmPassword();
    });

    passwordInput.addEventListener("input", function () {
      if (confirmPasswordInput.value) {
        scheduleConfirmPasswordCheck();
      }
    });
  }
});
