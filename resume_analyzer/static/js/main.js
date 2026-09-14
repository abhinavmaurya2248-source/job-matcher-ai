/**
 * Front-end helpers for the AI Resume Analyzer UI.
 * - Bootstrap-style client side validation feedback
 * - Selected file name / size display and PDF + 5 MB checks
 * - Loading state on the upload button
 */
(function () {
  "use strict";

  var MAX_BYTES = 5 * 1024 * 1024;

  // --- generic form validation styling -------------------------------------
  document.querySelectorAll("form.needs-validation").forEach(function (form) {
    form.addEventListener(
      "submit",
      function (event) {
        if (!form.checkValidity()) {
          event.preventDefault();
          event.stopPropagation();
        }
        form.classList.add("was-validated");
      },
      false
    );
  });

  // --- upload page ---------------------------------------------------------
  var uploadForm = document.getElementById("upload-form");
  if (!uploadForm) return;

  var input = document.getElementById("resume");
  var info = document.getElementById("file-info");
  var nameEl = document.getElementById("file-name");
  var sizeEl = document.getElementById("file-size");
  var errorBox = document.getElementById("client-error");
  var spinner = document.getElementById("submit-spinner");
  var label = document.getElementById("submit-label");
  var button = document.getElementById("submit-btn");

  function showError(message) {
    errorBox.textContent = message;
    errorBox.classList.remove("d-none");
  }

  function clearError() {
    errorBox.textContent = "";
    errorBox.classList.add("d-none");
  }

  function formatSize(bytes) {
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(2) + " MB";
  }

  input.addEventListener("change", function () {
    clearError();
    var file = input.files && input.files[0];
    if (!file) {
      info.classList.add("d-none");
      return;
    }
    nameEl.textContent = file.name;
    sizeEl.textContent = formatSize(file.size);
    info.classList.remove("d-none");

    if (!/\.pdf$/i.test(file.name)) {
      showError("Only PDF files are allowed.");
    } else if (file.size > MAX_BYTES) {
      showError("File is too large. Maximum allowed size is 5 MB.");
    }
  });

  uploadForm.addEventListener("submit", function (event) {
    var file = input.files && input.files[0];

    if (!file) {
      event.preventDefault();
      showError("Please choose a PDF resume before uploading.");
      return;
    }
    if (!/\.pdf$/i.test(file.name)) {
      event.preventDefault();
      showError("Only PDF files are allowed.");
      return;
    }
    if (file.size > MAX_BYTES) {
      event.preventDefault();
      showError("File is too large. Maximum allowed size is 5 MB.");
      return;
    }

    // Loading state - the server still performs its own validation.
    spinner.classList.remove("d-none");
    label.textContent = "Uploading...";
    button.setAttribute("disabled", "disabled");
    setTimeout(function () {
      button.removeAttribute("disabled");
    }, 8000);
  });
})();
