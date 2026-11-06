(function () {
  "use strict";

  // RF-7: one submission only (HU-006 pattern). Each admin form binds its own
  // flag; the first submit disables the button and marks the form as busy, and
  // any later submit is discarded. The `submit` event only fires once the HTML5
  // validation has passed, so native validation stays intact.
  function initAdminForms() {
    var forms = document.querySelectorAll(".admin__form");
    if (!forms.length) {
      return;
    }

    Array.prototype.forEach.call(forms, function (form) {
      var button = form.querySelector(".admin__submit");
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
    });
  }

  document.addEventListener("DOMContentLoaded", initAdminForms);
})();
