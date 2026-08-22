const registry = window.SOLOFORGE_REGISTRY || { sources: [], games: [] };

const state = {
  view: "dashboard",
  query: "",
  filter: "all",
  candidates: [],
  narrowed: false,
  installedScan: null,
  nativeScanActive: false,
};

const viewTitles = {
  dashboard: "Overview",
  installed: "Installed",
  registry: "Registry",
  sources: "Sources",
  builder: "Builder",
  about: "About",
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };
    return entities[character];
  });
}

function safeUrl(value) {
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) ? url.href : "#";
  } catch {
    return "#";
  }
}

function matchesQuery(record) {
  if (!state.query) return true;
  return JSON.stringify(record).toLowerCase().includes(state.query.toLowerCase());
}

function statusPill(status) {
  if (status === "approved" || status === "safe") return `<span class="pill pill-ok">${escapeHtml(status)}</span>`;
  if (status === "blocked") return `<span class="pill block">blocked</span>`;
  return `<span class="pill pill-warn">review</span>`;
}

function sourceHost(url) {
  try {
    return new URL(url).host;
  } catch {
    return url;
  }
}

function filteredGames() {
  return registry.games.filter((game) => {
    if (!matchesQuery(game)) return false;
    const reviewStatus = game.safety?.reviewStatus || "requiresManualReview";
    if (state.filter === "safe") return reviewStatus === "approved";
    if (state.filter === "review") return reviewStatus === "requiresManualReview";
    return true;
  });
}

function renderMetrics() {
  const games = registry.games.length;
  const sources = registry.sources.length;
  const features = registry.games.reduce((total, game) => total + (game.features || []).length, 0);
  const review = [...registry.sources, ...registry.games].filter(
    (record) => record.safety?.reviewStatus === "requiresManualReview",
  ).length;

  $("#metric-grid").innerHTML = [
    ["Games", games],
    ["Sources", sources],
    ["Features", features],
    ["Review", review],
  ]
    .map(([label, value]) => `<div class="metric"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");
}

function renderReviewList() {
  const reviewItems = [...registry.sources, ...registry.games]
    .filter((record) => record.safety?.reviewStatus === "requiresManualReview")
    .slice(0, 6);

  $("#review-list").innerHTML = reviewItems
    .map(
      (item) => `
        <div class="review-item">
          <div><strong>${escapeHtml(item.name)}</strong><br>${escapeHtml(item.source.importMode)} · ${escapeHtml(item.source.license)}</div>
          ${statusPill(item.safety.reviewStatus)}
        </div>
      `,
    )
    .join("");
}

function renderGames() {
  const games = filteredGames();
  $("#game-grid").innerHTML = games
    .map(
      (game) => `
        <article class="game-card">
          <header>
            <div>
              <h4>${escapeHtml(game.name)}</h4>
              <div class="meta-row">
                ${(game.game?.platforms || []).map((platform) => `<span class="pill">${escapeHtml(platform)}</span>`).join("")}
              </div>
            </div>
            ${statusPill(game.safety.reviewStatus)}
          </header>
          <ul class="features">
            ${(game.features || [])
              .map(
                (feature) => `
                  <li>
                    <span>${escapeHtml(feature.name)}</span>
                    ${statusPill(feature.safetyStatus)}
                  </li>
                `,
              )
              .join("")}
          </ul>
          <div class="meta-row">
            <span class="pill">${escapeHtml(game.source.importMode)}</span>
            <span class="pill">${escapeHtml(game.source.license)}</span>
          </div>
        </article>
      `,
    )
    .join("");
}

function renderSources() {
  const sources = registry.sources.filter(matchesQuery);
  $("#sources-table").innerHTML = sources
    .map(
      (record) => `
        <tr>
          <td>${escapeHtml(record.name)}</td>
          <td>${escapeHtml(record.source.importMode)}</td>
          <td>${escapeHtml(record.source.license)}</td>
          <td>${statusPill(record.safety.reviewStatus)}</td>
          <td><a href="${escapeHtml(safeUrl(record.source.url))}" target="_blank" rel="noreferrer">${escapeHtml(sourceHost(record.source.url))}</a></td>
        </tr>
      `,
    )
    .join("");
}

function renderInstalled() {
  const scan = state.installedScan;
  const games = scan?.games || [];
  const matched = games.filter((game) => game.match).length;
  const playable = games.filter((game) => game.availableFeatures?.length).length;
  const libraries = scan?.libraries?.length || 0;

  $("#installed-metrics").innerHTML = [
    ["Installed", games.length],
    ["Matched", matched],
    ["With tools", playable],
    ["Libraries", libraries],
  ]
    .map(([label, value]) => `<div class="metric"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");

  if (!scan) {
    $("#installed-list").innerHTML = `
      <div class="panel">
        <h4>No scan imported</h4>
        <p>Import a launcher scan JSON file, or run the native scanner from the Windows, Linux, or macOS app.</p>
      </div>
    `;
    return;
  }

  const visibleGames = games.filter(matchesQuery);
  if (!visibleGames.length) {
    $("#installed-list").innerHTML = `
      <div class="panel">
        <h4>No launcher games found</h4>
        <p>The scan completed, but no matching local Steam, GOG, Ubisoft Connect, or EA App metadata was found.</p>
      </div>
    `;
    return;
  }

  $("#installed-list").innerHTML = visibleGames
    .map((game) => {
      const featureText = game.availableFeatures?.length ? game.availableFeatures.join(", ") : "Review needed";
      const launcher = game.launcher || "steam";
      const idLabel = launcher === "steam" ? "Steam AppID" : `${launcher} ID`;
      const storeId = game.storeId || game.appid || "unknown";
      const reviewStatus = game.safetyStatus || "requiresManualReview";
      return `
        <article class="installed-item">
          <div>
            <strong>${escapeHtml(game.name)}</strong>
            <span>${escapeHtml(idLabel)} ${escapeHtml(storeId)}</span>
          </div>
          <div>${game.match ? statusPill(reviewStatus) : statusPill("requiresManualReview")}</div>
          <div><span>${escapeHtml(featureText)}</span></div>
        </article>
      `;
    })
    .join("");
}

async function importInstalledScan(file) {
  try {
    const text = await file.text();
    const scan = JSON.parse(text);
    if (!Array.isArray(scan.games)) {
      throw new Error("Invalid SoloForge launcher or Steam library JSON");
    }
    if (!Array.isArray(scan.libraries)) scan.libraries = [];
    state.installedScan = scan;
    $("#installed-status").textContent = `Imported scan: ${scan.games.length} game(s), ${scan.libraries.length} library location(s).`;
    renderInstalled();
  } catch (error) {
    $("#installed-list").innerHTML = `
      <div class="panel">
        <h4>Import failed</h4>
        <p>${escapeHtml(error.message)}</p>
      </div>
    `;
  }
}

function nativeBridge() {
  return window.soloforgeNative || window.webkit?.messageHandlers?.soloforge;
}

function nativePlatformLabel() {
  const platform = window.soloforgeNative?.platform;
  if (platform === "win32") return "Windows PC";
  if (platform === "linux") return "Linux PC";
  if (platform === "darwin") return "Mac";
  return "PC";
}

async function requestNativeScan() {
  const bridge = nativeBridge();
  if (!bridge) {
    $("#installed-status").textContent = "Native scanner is available in the Windows, Linux, and macOS app builds.";
    return;
  }
  state.nativeScanActive = true;
  $("#installed-status").textContent = `Scanning local launcher metadata on this ${nativePlatformLabel()}...`;

  if (window.soloforgeNative?.scanInstalledGames) {
    try {
      const result = await window.soloforgeNative.scanInstalledGames();
      handleNativeScan({ detail: result });
    } catch (error) {
      handleNativeScan({ detail: { ok: false, error: error.message || String(error) } });
    }
    return;
  }

  bridge.postMessage({ type: "scanInstalledGames" });
}

function handleNativeScan(event) {
  state.nativeScanActive = false;
  if (!event.detail?.ok) {
    $("#installed-status").textContent = event.detail?.error || "Native scan failed.";
    return;
  }
  if (!Array.isArray(event.detail.payload?.games) || !Array.isArray(event.detail.payload?.libraries)) {
    $("#installed-status").textContent = "Native scan returned invalid launcher data.";
    return;
  }
  state.installedScan = event.detail.payload;
  $("#installed-status").textContent = `Scan complete: ${state.installedScan.games.length} game(s), ${state.installedScan.libraries.length} library location(s).`;
  renderInstalled();
}

function renderBuilderSelect() {
  $("#builder-game").innerHTML = [
    `<option value="">Custom offline game</option>`,
    ...registry.games.map((game) => `<option value="${escapeHtml(game.id)}">${escapeHtml(game.name)}</option>`),
  ].join("");
}

function makeCandidates(value, valueType) {
  const base = Number(value) || 0;
  const count = 64;
  return Array.from({ length: count }, (_, index) => {
    const offset = (index + 11).toString(16).padStart(4, "0").toUpperCase();
    const nearby = index % 5 === 0 ? base : base + ((index % 9) - 4) * 2;
    return {
      address: `0x7FF6A2${offset}`,
      value: nearby,
      type: valueType,
    };
  });
}

function firstScan() {
  const value = $("#scan-value").value;
  const valueType = $("#value-type").value;
  state.candidates = makeCandidates(value, valueType);
  state.narrowed = false;
  $("#scan-status").textContent = `${state.candidates.length} candidates`;
  renderCandidates();
}

function narrowScan() {
  if (!state.candidates.length) {
    $("#scan-status").textContent = "Run first scan";
    return;
  }

  const changed = Number($("#changed-value").value) || 0;
  state.candidates = state.candidates
    .filter((candidate, index) => index % 5 === 0 || index % 13 === 0)
    .map((candidate, index) => ({
      ...candidate,
      value: index < 4 ? changed : changed + index,
    }))
    .slice(0, state.narrowed ? 4 : 13);
  state.narrowed = true;
  $("#scan-status").textContent = `${state.candidates.length} candidates`;
  renderCandidates();
}

function saveDraft() {
  const gameId = $("#builder-game").value;
  const game = registry.games.find((item) => item.id === gameId);
  const customName = $("#custom-game").value.trim();
  const strictlyMultiplayer = $("#custom-multiplayer").checked;
  if (strictlyMultiplayer) {
    $("#scan-status").textContent = "Blocked: strictly multiplayer games are outside SoloForge.";
    return;
  }
  if (!game && !customName) {
    $("#scan-status").textContent = "Choose a registry game or enter a custom singleplayer game.";
    return;
  }
  const draft = {
    name: "Local Value Editor",
    gameId: gameId || null,
    gameName: game?.name || customName,
    offlineOnly: true,
    singleplayerOnly: true,
    multiplayerBlocked: true,
    achievementCompatibility: "neutral-by-policy",
    storage: "local-only",
    valueType: $("#value-type").value,
    candidates: state.candidates.slice(0, 4),
    savedAt: new Date().toISOString(),
  };
  const existing = JSON.parse(localStorage.getItem("soloforgeDrafts") || "[]");
  existing.push(draft);
  localStorage.setItem("soloforgeDrafts", JSON.stringify(existing));
  $("#scan-status").textContent = `Saved ${draft.name}`;
}

function renderCandidates() {
  $("#candidate-count").textContent = String(state.candidates.length);
  $("#candidate-list").innerHTML = state.candidates
    .slice(0, 20)
    .map(
      (candidate) => `
        <div class="candidate">
          <div><strong>${escapeHtml(candidate.address)}</strong><br>${escapeHtml(candidate.type)}</div>
          <span>${escapeHtml(candidate.value)}</span>
        </div>
      `,
    )
    .join("");
}

function setView(view) {
  state.view = view;
  $("#view-title").textContent = viewTitles[view] || view;
  $$(".view").forEach((element) => element.classList.toggle("is-visible", element.id === `${view}-view`));
  $$(".nav-button").forEach((button) => button.classList.toggle("is-active", button.dataset.view === view));
}

function renderAll() {
  renderMetrics();
  renderReviewList();
  renderGames();
  renderSources();
  renderInstalled();
  renderBuilderSelect();
  renderCandidates();
}

function bindEvents() {
  $$(".nav-button").forEach((button) => {
    button.addEventListener("click", () => setView(button.dataset.view));
  });

  $$(".segment").forEach((button) => {
    button.addEventListener("click", () => {
      state.filter = button.dataset.filter;
      $$(".segment").forEach((item) => item.classList.toggle("is-active", item === button));
      renderGames();
    });
  });

  $("#search-input").addEventListener("input", (event) => {
    state.query = event.target.value;
    renderGames();
    renderSources();
    renderInstalled();
  });

  $("#installed-import").addEventListener("change", (event) => {
    const [file] = event.target.files;
    if (file) importInstalledScan(file);
  });

  $("#native-scan").addEventListener("click", requestNativeScan);
  window.addEventListener("soloforge-native-scan", handleNativeScan);

  $("#first-scan").addEventListener("click", firstScan);
  $("#narrow-scan").addEventListener("click", narrowScan);
  $("#save-draft").addEventListener("click", saveDraft);
}

bindEvents();
renderAll();
