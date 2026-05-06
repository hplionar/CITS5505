document.addEventListener("DOMContentLoaded", function () {
  const calendarDays = document.querySelectorAll(".calendar-grid button");

  calendarDays.forEach(function (day) {
    day.addEventListener("click", function () {
      calendarDays.forEach(function (button) {
        button.classList.remove("selected");
      });

      day.classList.add("selected");
    });
  });
});