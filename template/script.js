// Client-side search
(function () {
  var body = document.body;

  // Appearance (saved in localStorage)
  var settings = {};
  try { settings = JSON.parse(localStorage.getItem("pptos-wiki-appearance") || "{}"); } catch (e) { settings = {}; }
  function applyAppearance() {
    body.setAttribute("data-text-size", settings.textSize || "standard");
    body.setAttribute("data-width", settings.width || "standard");
    body.setAttribute("data-color", settings.color || "automatic");
    var text = document.querySelector('input[name="text-size"][value="' + (settings.textSize || "standard") + '"]');
    var width = document.querySelector('input[name="width"][value="' + (settings.width || "standard") + '"]');
    var color = document.querySelector('input[name="color"][value="' + (settings.color || "automatic") + '"]');
    if (text) text.checked = true;
    if (width) width.checked = true;
    if (color) color.checked = true;
  }
  function saveAppearance() { try { localStorage.setItem("pptos-wiki-appearance", JSON.stringify(settings)); } catch (e) {} }
  document.querySelectorAll('input[name="text-size"]').forEach(function (el) {
    el.addEventListener("change", function () { settings.textSize = el.value; saveAppearance(); applyAppearance(); });
  });
  document.querySelectorAll('input[name="width"]').forEach(function (el) {
    el.addEventListener("change", function () { settings.width = el.value; saveAppearance(); applyAppearance(); });
  });
  document.querySelectorAll('input[name="color"]').forEach(function (el) {
    el.addEventListener("change", function () { settings.color = el.value; saveAppearance(); applyAppearance(); });
  });
  applyAppearance();

  // Contents toggle (narrow screens)
  var contentsToggle = document.getElementById("contentsToggle");
  if (contentsToggle) contentsToggle.addEventListener("click", function () { body.classList.remove("show-appearance"); body.classList.toggle("show-contents"); });

  // Appearance toggle (narrow screens)
  var appearanceToggle = document.getElementById("appearanceToggle");
  if (appearanceToggle) appearanceToggle.addEventListener("click", function () { body.classList.remove("show-contents"); body.classList.toggle("show-appearance"); });

  // Tapping a Contents link jumps to that section and closes the panel
  document.querySelectorAll(".contents-box a").forEach(function (a) {
    a.addEventListener("click", function () { body.classList.remove("show-contents"); });
  });

  // Search
  var searchInput = document.getElementById("searchInput");
  var searchResults = document.getElementById("searchResults");
  var searchIndex = null;
  function loadIndex(callback) {
    if (searchIndex) return callback(searchIndex);
    fetch("/search.json").then(function (r) { return r.json(); }).then(function (data) {
      searchIndex = data;
      callback(data);
    }).catch(function () { callback([]); });
  }
  function renderResults(query) {
    if (!query || query.length < 2) { searchResults.hidden = true; searchResults.innerHTML = ""; return; }
    loadIndex(function (index) {
      var q = query.toLowerCase();
      // Ranking:
      // exact title, then title starting with the query, then title
      // containing it, then pages that only mention it in the text.
      function rank(page) {
        var title = page.title.toLowerCase();
        if (title === q) return 0;
        if (title.indexOf(q) === 0) return 1;
        if (title.indexOf(q) !== -1) return 2;
        return 3;
      }
      var matches = index.filter(function (page) {
        return (page.title + " " + page.text).toLowerCase().indexOf(q) !== -1;
      }).sort(function (a, b) { return rank(a) - rank(b); }).slice(0, 8);
      if (!matches.length) { searchResults.hidden = true; searchResults.innerHTML = ""; return; }
      searchResults.innerHTML = matches.map(function (page) {
        var safeTitle = page.title.replace(/</g, "&lt;");
        var safePath = page.path.replace(/</g, "&lt;");
        return '<a href="' + safePath + '">' + safeTitle +
          '<div class="result-path">wiki.pptos.net' + safePath + '</div></a>';
      }).join("");
      searchResults.hidden = false;
    });
  }
  if (searchInput) {
    searchInput.addEventListener("input", function () { renderResults(searchInput.value.trim()); });
    searchInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        var first = searchResults.querySelector("a");
        if (first) window.location.href = first.getAttribute("href");
      }
      if (e.key === "Escape") { searchResults.hidden = true; }
    });
    document.addEventListener("click", function (e) {
      if (!e.target.closest(".search")) searchResults.hidden = true;
    });
  }
  var searchButton = document.getElementById("searchButton");
  if (searchButton) searchButton.addEventListener("click", function () { renderResults(searchInput.value.trim()); });

  // Fullscreen image viewer
  var viewer = document.getElementById("mediaViewer");
  var viewerImage = document.getElementById("viewerImage");
  var viewerCaption = document.getElementById("viewerCaption");
  var viewerInfo = document.getElementById("viewerInfo");
  var images = Array.prototype.slice.call(document.querySelectorAll(".article-body img, .infobox img"));
  var currentIndex = 0;
  function openViewer(index) {
    if (!images[index]) return;
    currentIndex = index;
    var img = images[index];
    viewerImage.src = img.getAttribute("src");
    viewerImage.alt = img.getAttribute("alt") || "";
    var fig = img.closest("figure");
    var caption = "";
    if (fig) { var cap = fig.querySelector("figcaption"); if (cap) caption = cap.textContent; }
    if (!caption) caption = img.getAttribute("alt") || img.getAttribute("title") || "";
    viewerCaption.textContent = caption;
    viewerInfo.textContent = (index + 1) + " / " + images.length + "  ·  " + img.getAttribute("src");
    viewer.hidden = false;
    document.body.style.overflow = "hidden";
  }
  function closeViewer() { viewer.hidden = true; document.body.style.overflow = ""; }
  function stepViewer(delta) { openViewer((currentIndex + delta + images.length) % images.length); }
  images.forEach(function (img, i) {
    img.addEventListener("click", function () { openViewer(i); });
    img.style.cursor = "zoom-in";
  });
  document.getElementById("viewerClose").addEventListener("click", closeViewer);
  document.getElementById("viewerPrev").addEventListener("click", function () { stepViewer(-1); });
  document.getElementById("viewerNext").addEventListener("click", function () { stepViewer(1); });
  viewer.addEventListener("click", function (e) { if (e.target === viewer) closeViewer(); });
  document.addEventListener("keydown", function (e) {
    if (viewer.hidden) return;
    if (e.key === "Escape") closeViewer();
    if (e.key === "ArrowLeft") stepViewer(-1);
    if (e.key === "ArrowRight") stepViewer(1);
  });
})();
