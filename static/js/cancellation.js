(function () {
  "use strict";

  // RF-10: one submission only (HU-006 pattern). The first submit is
  // intercepted to disable the button and mark the form as busy; the second
  // one is discarded. No new user-facing copy is introduced.
  function initCancellationSubmit() {
    var form = document.querySelector(".cancellation__form");
    if (!form) {
      return;
    }
    var button = form.querySelector(".cancellation__submit");
    var submitting = false;

    form.addEventListener("submit", function (event) {
      if (submitting) {
        event.preventDefault();
        return;
      }
      submitting = true;
      event.preventDefault();
      if (button) {
        button.disabled = true;
        button.setAttribute("aria-busy", "true");
      }
      form.setAttribute("aria-busy", "true");
      form.submit();
    });
  }

  document.addEventListener("DOMContentLoaded", initCancellationSubmit);
})();
