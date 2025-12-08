// Helper: theme toggle with localStorage
function applyStoredTheme() {
  const stored = localStorage.getItem("studio-theme");
  const html = document.documentElement;
  if (stored === "light" || stored === "dark") {
    html.setAttribute("data-theme", stored);
  } else {
    html.setAttribute("data-theme", "dark");
  }
}

function toggleTheme() {
  const html = document.documentElement;
  const current = html.getAttribute("data-theme") || "dark";
  const next = current === "dark" ? "light" : "dark";
  html.setAttribute("data-theme", next);
  localStorage.setItem("studio-theme", next);
}

function setupThemeToggle() {
  applyStoredTheme();
  document.querySelectorAll("#themeToggle").forEach((btn) => {
    btn.addEventListener("click", toggleTheme);
  });
}

// Loader
function setupLoader() {
  const loader = document.getElementById("global-loader");
  if (!loader) return;
  window.addEventListener("load", () => {
    setTimeout(() => {
      loader.classList.add("hidden");
    }, 600);
  });
}

// Convert YouTube link to embeddable URL
function toEmbedUrl(url) {
  if (!url) return "";
  try {
    // youtu.be short
    if (url.includes("youtu.be/")) {
      const id = url.split("youtu.be/")[1].split(/[?&]/)[0];
      return "https://www.youtube.com/embed/" + id + "?autoplay=1";
    }
    // watch?v=
    const u = new URL(url);
    const v = u.searchParams.get("v");
    if (v) {
      return "https://www.youtube.com/embed/" + v + "?autoplay=1";
    }
    // already embed
    if (url.includes("/embed/")) return url + "?autoplay=1";
  } catch (e) {
    console.warn("Bad YouTube URL", e);
  }
  return url;
}

// Player modal handlers
function setupPlayerModal() {
  const modal = document.getElementById("playerModal");
  if (!modal) return;
  const frame = document.getElementById("playerFrame");
  const titleEl = document.getElementById("playerTitle");

  function openPlayer(songLink, title) {
    const embed = toEmbedUrl(songLink);
    if (!embed) return;
    frame.src = embed;
    titleEl.textContent = title || "Now Playing";
    modal.classList.remove("hidden");
  }

  function closePlayer() {
    modal.classList.add("hidden");
    frame.src = "";
  }

  modal.querySelectorAll("[data-close]").forEach((btn) => {
    btn.addEventListener("click", closePlayer);
  });
  modal.addEventListener("click", (e) => {
    if (e.target === modal) closePlayer();
  });

  document.querySelectorAll(".open-project").forEach((btn) => {
    btn.addEventListener("click", () => {
      const link = btn.getAttribute("data-song-link");
      const title = btn.getAttribute("data-title");
      openPlayer(link, title);
    });
  });
}

// Global search
function setupSearch() {
  const input = document.getElementById("globalSearch");
  const resultsBox = document.getElementById("searchResults");
  if (!input || !resultsBox) return;

  let debounceTimer = null;

  function hideResults() {
    resultsBox.classList.remove("visible");
    resultsBox.innerHTML = "";
  }

  input.addEventListener("input", () => {
    const q = input.value.trim();
    if (debounceTimer) clearTimeout(debounceTimer);
    if (!q) {
      hideResults();
      return;
    }
    debounceTimer = setTimeout(async () => {
      const res = await fetch(`/search?q=${encodeURIComponent(q)}`);
      const json = await res.json();
      const items = json.results || [];
      if (!items.length) {
        hideResults();
        return;
      }
      resultsBox.innerHTML = items
        .map(
          (r) => `
          <div class="search-result-item" data-type="${r.type}" data-id="${
            r.id
          }" data-song-link="${r.song_link || ""}">
            <span>${r.label}</span>
            <span class="type">${r.type}</span>
          </div>
        `
        )
        .join("");
      resultsBox.classList.add("visible");
    }, 220);
  });

  document.addEventListener("click", (e) => {
    if (!resultsBox.contains(e.target) && e.target !== input) {
      hideResults();
    }
  });

  resultsBox.addEventListener("click", (e) => {
    const item = e.target.closest(".search-result-item");
    if (!item) return;
    const type = item.dataset.type;
    const id = item.dataset.id;
    const songLink = item.dataset.songLink;

    if (type === "artist") {
      const section = document.getElementById("artists-section");
      section?.scrollIntoView({ behavior: "smooth", block: "start" });
    } else if (type === "production") {
      const section = document.getElementById("productions-section");
      section?.scrollIntoView({ behavior: "smooth", block: "start" });
    } else if (type === "distributor") {
      const section = document.getElementById("distributors-section");
      section?.scrollIntoView({ behavior: "smooth", block: "start" });
    } else if (type === "project" && songLink) {
      // Trigger player directly
      const embed = toEmbedUrl(songLink);
      const modal = document.getElementById("playerModal");
      const frame = document.getElementById("playerFrame");
      const titleEl = document.getElementById("playerTitle");
      if (modal && frame && titleEl) {
        frame.src = embed;
        titleEl.textContent = item.textContent.trim();
        modal.classList.remove("hidden");
      }
    }
    hideResults();
  });
}

// Insert / Delete modal
function setupManageModal() {
  const modal = document.getElementById("manageModal");
  if (!modal) return;

  const titleEl = document.getElementById("manageTitle");
  const form = document.getElementById("manageForm");
  const messageEl = document.getElementById("manageMessage");
  const submitBtn = document.getElementById("manageSubmit");
  const tabs = modal.querySelectorAll(".manage-tab");

  let mode = "insert"; // or "delete"
  let entity = "artist";

  const btnInsert = document.getElementById("btnOpenInsert");
  const btnDelete = document.getElementById("btnOpenDelete");

  function openModal(newMode) {
    mode = newMode;
    titleEl.textContent =
      mode === "insert" ? "Insert new record" : "Delete record";
    messageEl.textContent = "";
    messageEl.className = "manage-message";
    modal.classList.remove("hidden");
    renderFields();
  }

  function closeModal() {
    modal.classList.add("hidden");
  }

  function setEntity(newEntity) {
    entity = newEntity;
    renderFields();
  }

  function renderFields() {
    // For delete mode, just ask for ID
    if (mode === "delete") {
      form.innerHTML = `
        <label class="full-span">
          ID to delete (${entity}_id)
          <input type="text" name="id" required />
        </label>
      `;
      return;
    }

    // Insert mode fields by entity
    if (entity === "artist") {
      form.innerHTML = `
        <label>
          Artist ID
          <input type="text" name="artist_id" required />
        </label>
        <label>
          Name
          <input type="text" name="name" required />
        </label>
        <label class="full-span">
          Photo URL
          <input type="text" name="photo_url" />
        </label>
        <label class="full-span">
          Last Project ID
          <input type="text" name="last_project_id" />
        </label>
      `;
    } else if (entity === "project") {
      form.innerHTML = `
        <label>
          Project ID
          <input type="text" name="project_id" required />
        </label>
        <label>
          Title
          <input type="text" name="title" />
        </label>
        <label>
          Type
          <input type="text" name="type" />
        </label>
        <label>
          Release Date (YYYY-MM-DD)
          <input type="text" name="release_date" />
        </label>
        <label class="full-span">
          Song Link (YouTube URL)
          <input type="text" name="song_link" />
        </label>
        <label class="full-span">
          Album Art URL
          <input type="text" name="album_art" />
        </label>
        <label class="full-span">
          Description
          <textarea name="description"></textarea>
        </label>
      `;
    } else if (entity === "production") {
      form.innerHTML = `
        <label>
          Production ID
          <input type="text" name="production_id" required />
        </label>
        <label>
          Name
          <input type="text" name="name" required />
        </label>
        <label>
          Logo URL
          <input type="text" name="logo_url" />
        </label>
        <label>
          Market Value
          <input type="number" name="market_value" />
        </label>
        <label class="full-span">
          Last Project ID
          <input type="text" name="last_project_id" />
        </label>
      `;
    } else if (entity === "distributor") {
      form.innerHTML = `
        <label>
          Distributor ID
          <input type="text" name="distributor_id" required />
        </label>
        <label>
          Name
          <input type="text" name="name" required />
        </label>
        <label>
          Logo URL
          <input type="text" name="logo_url" />
        </label>
        <label>
          Market Value
          <input type="number" name="market_value" />
        </label>
        <label class="full-span">
          Website URL
          <input type="text" name="url" />
        </label>
      `;
    }
  }

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      setEntity(tab.dataset.entity);
    });
  });

  submitBtn.addEventListener("click", async () => {
    messageEl.textContent = "";
    messageEl.className = "manage-message";

    const payload = { entity };

    if (mode === "delete") {
      const idField = form.querySelector("input[name='id']");
      if (!idField.value.trim()) return;
      payload.id = idField.value.trim();
      try {
        const res = await fetch("/api/delete", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const json = await res.json();
        if (json.ok) {
          messageEl.textContent = "Deleted successfully. Reload to see changes.";
          messageEl.classList.add("ok");
        } else {
          messageEl.textContent = json.message || "Error while deleting.";
          messageEl.classList.add("err");
        }
      } catch (e) {
        messageEl.textContent = "Request failed.";
        messageEl.classList.add("err");
      }
      return;
    }

    // Insert mode
    const formData = new FormData(form);
    const data = {};
    formData.forEach((val, key) => {
      if (val !== "") data[key] = val;
    });
    payload.data = data;

    try {
      const res = await fetch("/api/insert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const json = await res.json();
      if (json.ok) {
        messageEl.textContent = "Inserted successfully. Reload to see it in UI.";
        messageEl.classList.add("ok");
      } else {
        messageEl.textContent = json.message || "Error while inserting.";
        messageEl.classList.add("err");
      }
    } catch (e) {
      messageEl.textContent = "Request failed.";
      messageEl.classList.add("err");
    }
  });

  modal.querySelectorAll("[data-close]").forEach((btn) => {
    btn.addEventListener("click", closeModal);
  });
  modal.addEventListener("click", (e) => {
    if (e.target === modal) closeModal();
  });

  btnInsert?.addEventListener("click", () => openModal("insert"));
  btnDelete?.addEventListener("click", () => openModal("delete"));
}

// ------------- INIT ------------- //

document.addEventListener("DOMContentLoaded", () => {
  setupThemeToggle();
  setupLoader();
  setupPlayerModal();
  setupSearch();
  setupManageModal();
});
