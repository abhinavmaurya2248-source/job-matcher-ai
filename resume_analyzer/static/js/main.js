/**
 * Front-end helpers for the AI Resume Analyzer UI (no libraries).
 * - Navbar scroll state, scroll reveal, animated score ring / bars
 * - Bootstrap-style client side validation feedback
 * - Upload page: drag & drop, selected file display, PDF + 5 MB checks,
 *   job description character count, loading state
 * The server still performs all real validation and analysis.
 */
(function () {
  "use strict";

  document.documentElement.classList.add("js");
  var reduceMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // --- navbar background on scroll -----------------------------------------
  var nav = document.querySelector(".app-navbar");
  if (nav) {
    var onScroll = function () {
      nav.classList.toggle("is-scrolled", window.scrollY > 8);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  // --- scroll reveal + score ring / bars ------------------------------------
  // Values come from the server (data attributes / inline style); JS only
  // starts the visual transition when the element becomes visible.
  var animated = document.querySelectorAll(".reveal, .score-ring, .js-animate-bar");
  function show(el) {
    el.classList.add("is-visible");
    if (el.classList.contains("js-animate-bar")) el.classList.remove("js-animate-bar");
  }
  if (reduceMotion || !("IntersectionObserver" in window)) {
    animated.forEach(show);
  } else {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          show(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    animated.forEach(function (el) { observer.observe(el); });
  }

  // --- generic form validation styling -------------------------------------
  document.querySelectorAll("form.needs-validation").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add("was-validated");
    }, false);
  });

  // --- upload page ---------------------------------------------------------
  var uploadForm = document.getElementById("upload-form");
  if (!uploadForm) return;

  var MAX_BYTES = 5 * 1024 * 1024;
  var input = document.getElementById("resume");
  var zone = document.getElementById("dropzone");
  var info = document.getElementById("file-info");
  var nameEl = document.getElementById("file-name");
  var sizeEl = document.getElementById("file-size");
  var errorBox = document.getElementById("client-error");
  var spinner = document.getElementById("submit-spinner");
  var label = document.getElementById("submit-label");
  var button = document.getElementById("submit-btn");
  var jd = document.getElementById("job_description");
  var jdCount = document.getElementById("jd-count");

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

  function onFileChange() {
    clearError();
    var file = input.files && input.files[0];
    if (!file) {
      info.classList.add("d-none");
      if (zone) zone.classList.remove("has-file");
      return;
    }
    nameEl.textContent = file.name;
    sizeEl.textContent = formatSize(file.size);
    info.classList.remove("d-none");
    if (zone) zone.classList.add("has-file");

    if (!/\.pdf$/i.test(file.name)) {
      showError("Only PDF files are allowed.");
    } else if (file.size > MAX_BYTES) {
      showError("File is too large. Maximum allowed size is 5 MB.");
    }
  }
  input.addEventListener("change", onFileChange);

  // Drag & drop simply fills the same file input; the form posts as before.
  if (zone) {
    ["dragenter", "dragover"].forEach(function (type) {
      zone.addEventListener(type, function (event) {
        event.preventDefault();
        zone.classList.add("is-dragover");
      });
    });
    ["dragleave", "dragend", "drop"].forEach(function (type) {
      zone.addEventListener(type, function () { zone.classList.remove("is-dragover"); });
    });
    zone.addEventListener("drop", function (event) {
      event.preventDefault();
      var files = event.dataTransfer && event.dataTransfer.files;
      if (!files || !files.length) return;
      try {
        var dt = new DataTransfer();
        dt.items.add(files[0]);
        input.files = dt.files;
      } catch (e) {
        input.files = files;
      }
      onFileChange();
    });
  }

  if (jd && jdCount) {
    var updateCount = function () {
      var n = jd.value.length;
      jdCount.textContent = n.toLocaleString() + " character" + (n === 1 ? "" : "s");
    };
    jd.addEventListener("input", updateCount);
    updateCount();
  }

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

    // Loading state only - no fake progress; the server does the real work.
    spinner.classList.remove("d-none");
    label.textContent = "Analyzing your resume"; label.classList.add("btn-loading-dots");
    button.setAttribute("disabled", "disabled");
    setTimeout(function () { button.removeAttribute("disabled"); }, 15000);
  });
})();
