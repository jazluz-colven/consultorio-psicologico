(function () {
  "use strict";

  var MONTHS = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
  ];

  var calendarEl = document.getElementById("booking-calendar");
  var dateField = document.getElementById("booking-date");
  var gridEl = document.getElementById("calendar-grid");
  var monthEl = document.getElementById("calendar-month");
  var prevBtn = document.getElementById("calendar-prev");
  var nextBtn = document.getElementById("calendar-next");

  var todayISO = "";
  var selectedISO = "";
  var viewYear = 0;
  var viewMonth = 0;

  function pad(value) {
    return value < 10 ? "0" + value : String(value);
  }

  function toISO(year, month, day) {
    return year + "-" + pad(month + 1) + "-" + pad(day);
  }

  function fromISO(iso) {
    var parts = iso.split("-");
    return {
      year: parseInt(parts[0], 10),
      month: parseInt(parts[1], 10) - 1,
      day: parseInt(parts[2], 10),
    };
  }

  function isBookable(iso) {
    if (iso < todayISO) {
      return false;
    }
    var parts = fromISO(iso);
    var weekday = new Date(parts.year, parts.month, parts.day).getDay();
    return weekday >= 1 && weekday <= 5;
  }

  function renderCalendar() {
    if (!gridEl || !monthEl) {
      return;
    }
    monthEl.textContent = MONTHS[viewMonth] + " de " + viewYear;
    if (prevBtn) {
      var today = fromISO(todayISO);
      prevBtn.disabled =
        viewYear === today.year && viewMonth === today.month;
    }

    var first = new Date(viewYear, viewMonth, 1);
    var offset = (first.getDay() + 6) % 7;
    var total = new Date(viewYear, viewMonth + 1, 0).getDate();

    gridEl.innerHTML = "";
    var index;
    for (index = 0; index < offset; index += 1) {
      var blank = document.createElement("span");
      blank.className = "appointment__calendar-day is-blank";
      gridEl.appendChild(blank);
    }
    for (var day = 1; day <= total; day += 1) {
      (function (dayNumber) {
        var iso = toISO(viewYear, viewMonth, dayNumber);
        var button = document.createElement("button");
        button.type = "button";
        button.className = "appointment__calendar-day";
        button.textContent = String(dayNumber);
        button.setAttribute(
          "aria-label",
          dayNumber + " de " + MONTHS[viewMonth] + " de " + viewYear
        );
        if (!isBookable(iso)) {
          button.disabled = true;
          button.className += " is-disabled";
        } else {
          button.className += " is-bookable";
          button.addEventListener("click", function () {
            selectDate(iso);
          });
        }
        if (iso === selectedISO) {
          button.className += " is-selected";
          button.setAttribute("aria-pressed", "true");
        } else {
          button.setAttribute("aria-pressed", "false");
        }
        gridEl.appendChild(button);
      })(day);
    }
  }

  function selectDate(iso) {
    selectedISO = iso;
    if (dateField) {
      dateField.value = iso;
    }
    renderCalendar();
    refreshHours();
  }

  function changeMonth(delta) {
    var next = new Date(viewYear, viewMonth + delta, 1);
    viewYear = next.getFullYear();
    viewMonth = next.getMonth();
    renderCalendar();
  }

  function currentService() {
    var serviceField = document.getElementById("service");
    return serviceField ? serviceField.value : "";
  }

  function selectedTime() {
    var checked = document.querySelector(
      ".appointment__hour-input:checked"
    );
    return checked ? checked.value : "";
  }

  function createHour(hour, checked) {
    var label = document.createElement("label");
    label.className = "appointment__hour";
    var input = document.createElement("input");
    input.className = "appointment__hour-input";
    input.type = "radio";
    input.name = "time";
    input.value = hour;
    if (checked) {
      input.checked = true;
    }
    var text = document.createElement("span");
    text.textContent = hour;
    label.appendChild(input);
    label.appendChild(text);
    return label;
  }

  function fillBlock(blockId, hours, previous) {
    var block = document.getElementById(blockId);
    if (!block) {
      return;
    }
    block.innerHTML = "";
    hours.forEach(function (hour) {
      block.appendChild(createHour(hour, hour === previous));
    });
  }

  function fillHours(hours) {
    var previous = selectedTime();
    var morning = [];
    var afternoon = [];
    hours.forEach(function (hour) {
      if (hour < "12:00") {
        morning.push(hour);
      } else {
        afternoon.push(hour);
      }
    });
    fillBlock("hours-morning", morning, previous);
    fillBlock("hours-afternoon", afternoon, previous);

    var status = document.getElementById("hours-status");
    if (status) {
      status.textContent =
        hours.length === 0
          ? calendarEl.getAttribute("data-empty-message") || ""
          : "";
    }
  }

  function refreshHours() {
    if (!calendarEl || !dateField) {
      return;
    }
    var service = currentService();
    var date = dateField.value;
    var status = document.getElementById("hours-status");

    if (!service || !date) {
      fillBlock("hours-morning", [], "");
      fillBlock("hours-afternoon", [], "");
      if (status) {
        status.textContent = calendarEl.getAttribute("data-hint") || "";
      }
      return;
    }

    var url =
      "/citas/horarios?service=" +
      encodeURIComponent(service) +
      "&date=" +
      encodeURIComponent(date);

    fetch(url)
      .then(function (response) {
        if (!response.ok) {
          throw new Error("availability failed");
        }
        return response.json();
      })
      .then(function (data) {
        fillHours(data.available || []);
      })
      .catch(function () {
        fillHours([]);
      });
  }

  function initCalendar() {
    if (!calendarEl || !dateField || !gridEl) {
      return;
    }
    todayISO = calendarEl.getAttribute("data-today") || "";
    selectedISO = dateField.value || todayISO;

    var anchor = selectedISO ? fromISO(selectedISO) : fromISO(todayISO);
    viewYear = anchor.year;
    viewMonth = anchor.month;

    if (prevBtn) {
      prevBtn.addEventListener("click", function () {
        changeMonth(-1);
      });
    }
    if (nextBtn) {
      nextBtn.addEventListener("click", function () {
        changeMonth(1);
      });
    }

    renderCalendar();
  }

  document.addEventListener("DOMContentLoaded", function () {
    initCalendar();

    var serviceField = document.getElementById("service");
    if (serviceField) {
      serviceField.addEventListener("change", refreshHours);
    }

    if (calendarEl && dateField && serviceField && serviceField.value && dateField.value) {
      refreshHours();
    }
  });
})();
