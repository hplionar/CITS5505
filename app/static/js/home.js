document.addEventListener("DOMContentLoaded", function () {
  const calendarGrid = document.getElementById("calendarGrid");
  const calendarMonthLabel = document.getElementById("calendarMonthLabel");
  const selectedCalendarInfo = document.getElementById("selectedCalendarInfo");

  const prevMonthBtn = document.getElementById("prevMonthBtn");
  const nextMonthBtn = document.getElementById("nextMonthBtn");
  const openFullCalendarBtn = document.getElementById("openFullCalendarBtn");
  const calendarCard = document.getElementById("calendarCard");

  const joinedSessionsScript = document.getElementById("joinedSessionsData");

  let joinedSessions = [];

  if (joinedSessionsScript) {
    try {
      joinedSessions = JSON.parse(joinedSessionsScript.textContent);
    } catch (error) {
      joinedSessions = [];
    }
  }

  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  const dayNames = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];

  let currentMonth =
    Number(window.CSHUB_CALENDAR_START_MONTH || new Date().getMonth() + 1) - 1;

  let currentYear =
    Number(window.CSHUB_CALENDAR_START_YEAR || new Date().getFullYear());

  function formatDateKey(year, monthIndex, day) {
    const month = String(monthIndex + 1).padStart(2, "0");
    const date = String(day).padStart(2, "0");

    return year + "-" + month + "-" + date;
  }

  function getSessionsForDate(dateKey) {
    return joinedSessions.filter(function (session) {
      return session.reminder_date === dateKey;
    });
  }

  function formatSessionText(sessions) {
    if (!sessions || sessions.length === 0) {
      return "No joined Study Buddy session for this date.";
    }

    return sessions
      .map(function (session) {
        const mode = session.mode
          ? " · " + String(session.mode).replace("-", " ")
          : "";

        const location = session.location
          ? " · " + session.location
          : "";

        return session.topic + " at " + session.time + mode + location;
      })
      .join(" | ");
  }

  function renderSelectedDateInfo(date, sessions) {
    if (!selectedCalendarInfo) {
      return;
    }

    selectedCalendarInfo.innerHTML = "";

    const heading = document.createElement("strong");
    heading.textContent = date;
    selectedCalendarInfo.appendChild(heading);

    if (!sessions || sessions.length === 0) {
      const emptyText = document.createElement("p");
      emptyText.textContent = "No joined Study Buddy session for this date.";
      selectedCalendarInfo.appendChild(emptyText);
      return;
    }

    const list = document.createElement("div");
    list.className = "calendar-reminder-list";

    sessions.forEach(function (session) {
      const link = document.createElement("a");
      link.href = "/sessions/" + session.id;
      link.className = "calendar-reminder-item";

      const title = document.createElement("span");
      title.textContent = session.topic;

      const meta = document.createElement("small");
      meta.textContent = session.time + " - " + session.unit_code;

      link.appendChild(title);
      link.appendChild(meta);
      list.appendChild(link);
    });

    selectedCalendarInfo.appendChild(list);
  }

  function renderCalendar() {
    if (!calendarGrid || !calendarMonthLabel) {
      return;
    }

    calendarGrid.innerHTML = "";

    calendarMonthLabel.textContent =
      monthNames[currentMonth] + " " + currentYear;

    dayNames.forEach(function (day) {
      const dayHeader = document.createElement("span");
      dayHeader.textContent = day;
      calendarGrid.appendChild(dayHeader);
    });

    const firstDayOfMonth = new Date(currentYear, currentMonth, 1);
    const lastDayOfMonth = new Date(currentYear, currentMonth + 1, 0);

    const startDayIndex = firstDayOfMonth.getDay();
    const totalDays = lastDayOfMonth.getDate();

    const previousMonthLastDay =
      new Date(currentYear, currentMonth, 0).getDate();

    for (let i = startDayIndex - 1; i >= 0; i--) {
      const mutedButton = document.createElement("button");
      mutedButton.type = "button";
      mutedButton.className = "muted";
      mutedButton.textContent = previousMonthLastDay - i;
      mutedButton.dataset.sessionText =
        "This date is outside the selected month.";
      calendarGrid.appendChild(mutedButton);
    }

    for (let day = 1; day <= totalDays; day++) {
      const dateKey = formatDateKey(currentYear, currentMonth, day);
      const sessionsForDay = getSessionsForDate(dateKey);

      const dayButton = document.createElement("button");
      dayButton.type = "button";
      dayButton.textContent = day;
      dayButton.dataset.dateKey = dateKey;

      dayButton.dataset.date =
        day + " " + monthNames[currentMonth] + " " + currentYear;

      dayButton.dataset.sessionText = formatSessionText(sessionsForDay);

      if (sessionsForDay.length > 0) {
        dayButton.classList.add("event", "blue-event");
      }

      const today = new Date();
      const isToday =
        today.getDate() === day &&
        today.getMonth() === currentMonth &&
        today.getFullYear() === currentYear;

      if (isToday) {
        dayButton.classList.add("today");
      }

      calendarGrid.appendChild(dayButton);
    }

    const totalCellsWithoutHeaders = startDayIndex + totalDays;
    const remainingCells =
      totalCellsWithoutHeaders % 7 === 0
        ? 0
        : 7 - (totalCellsWithoutHeaders % 7);

    for (let day = 1; day <= remainingCells; day++) {
      const mutedButton = document.createElement("button");
      mutedButton.type = "button";
      mutedButton.className = "muted";
      mutedButton.textContent = day;
      mutedButton.dataset.sessionText =
        "This date is outside the selected month.";
      calendarGrid.appendChild(mutedButton);
    }

    attachCalendarClickEvents();
  }

  function attachCalendarClickEvents() {
    const calendarDays = document.querySelectorAll(".calendar-grid button");

    calendarDays.forEach(function (day) {
      day.addEventListener("click", function () {
        calendarDays.forEach(function (button) {
          button.classList.remove("selected");
        });

        day.classList.add("selected");

        const date = day.dataset.date;
        const sessionText = day.dataset.sessionText;

        if (!selectedCalendarInfo) {
          return;
        }

        if (date && sessionText) {
          renderSelectedDateInfo(date, getSessionsForDate(day.dataset.dateKey));
        } else if (sessionText) {
          selectedCalendarInfo.textContent = sessionText;
        } else {
          selectedCalendarInfo.textContent =
            "No joined Study Buddy session for this date.";
        }
      });
    });
  }

  if (prevMonthBtn) {
    prevMonthBtn.addEventListener("click", function () {
      currentMonth--;

      if (currentMonth < 0) {
        currentMonth = 11;
        currentYear--;
      }

      renderCalendar();

      if (selectedCalendarInfo) {
        selectedCalendarInfo.textContent =
          "Click a highlighted date to view your joined Study Buddy session.";
      }
    });
  }

  if (nextMonthBtn) {
    nextMonthBtn.addEventListener("click", function () {
      currentMonth++;

      if (currentMonth > 11) {
        currentMonth = 0;
        currentYear++;
      }

      renderCalendar();

      if (selectedCalendarInfo) {
        selectedCalendarInfo.textContent =
          "Click a highlighted date to view your joined Study Buddy session.";
      }
    });
  }

  if (openFullCalendarBtn && calendarCard) {
    openFullCalendarBtn.addEventListener("click", function () {
      calendarCard.classList.toggle("calendar-expanded");

      if (calendarCard.classList.contains("calendar-expanded")) {
        openFullCalendarBtn.textContent = "Close full calendar";
      } else {
        openFullCalendarBtn.textContent = "Open full calendar";
      }
    });
  }

  renderCalendar();
});
