(function () {
  "use strict";

  function refreshHours() {
    var serviceField = document.getElementById("service");
    var dateField = document.getElementById("date");
    var timeField = document.getElementById("time");
    var status = document.getElementById("hours-status");
    if (!serviceField || !dateField || !timeField) {
      return;
    }

    var service = serviceField.value;
    var date = dateField.value;
    if (!service || !date) {
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
        fillHours(timeField, status, data.available || []);
      })
      .catch(function () {
        fillHours(timeField, status, []);
      });
  }

  function fillHours(timeField, status, hours) {
    var previous = timeField.value;
    while (timeField.options.length > 1) {
      timeField.remove(1);
    }
    hours.forEach(function (hour) {
      var option = document.createElement("option");
      option.value = hour;
      option.textContent = hour;
      timeField.appendChild(option);
    });
    if (status) {
      status.textContent =
        hours.length === 0 ? timeField.getAttribute("data-empty-message") : "";
    }
    if (previous && hours.indexOf(previous) !== -1) {
      timeField.value = previous;
    } else {
      timeField.selectedIndex = 0;
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var serviceField = document.getElementById("service");
    var dateField = document.getElementById("date");
    if (!serviceField || !dateField) {
      return;
    }
    serviceField.addEventListener("change", refreshHours);
    dateField.addEventListener("change", refreshHours);
    if (serviceField.value && dateField.value) {
      refreshHours();
    }
  });
})();
