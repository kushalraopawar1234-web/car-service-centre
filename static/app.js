/* Car Service Centre - small progressive enhancements only. */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    /* Mobile navigation */
    var toggle = document.querySelector(".nav-toggle");
    var nav = document.getElementById("main-nav");

    if (toggle && nav) {
      toggle.addEventListener("click", function () {
        var open = nav.classList.toggle("open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
      });

      nav.addEventListener("click", function (event) {
        if (event.target.tagName === "A" && window.innerWidth <= 1060) {
          nav.classList.remove("open");
          toggle.setAttribute("aria-expanded", "false");
        }
      });
    }

    /* Confirm dialogs for destructive POST forms */
    document.querySelectorAll("form[data-confirm]").forEach(function (form) {
      form.addEventListener("submit", function (event) {
        if (!window.confirm(form.getAttribute("data-confirm"))) {
          event.preventDefault();
        }
      });
    });

    /* Flash message dismissal */
    document.querySelectorAll(".flash-close").forEach(function (button) {
      button.addEventListener("click", function () {
        var flash = button.closest(".flash");
        if (flash) {
          flash.remove();
        }
      });
    });

    document.querySelectorAll(".flash-success").forEach(function (flash) {
      window.setTimeout(function () {
        flash.remove();
      }, 7000);
    });

    /* Print buttons */
    var printBill = document.getElementById("print-bill");
    if (printBill) {
      printBill.addEventListener("click", function () {
        window.print();
      });
    }

    var printReports = document.getElementById("print-reports");
    if (printReports) {
      printReports.addEventListener("click", function () {
        window.print();
      });
    }
  });
})();
