const registry = window.SOLOFORGE_REGISTRY || { sources: [], games: [] };

const state = {
  view: "dashboard",
  query: "",
  filter: "all",
  candidates: [],
  narrowed: false,
};

const viewTitles = {
  dashboard: "Overview",
  registry: "Registry",
  sources: "Sources",
  builder: "Builder",
  about: "About",
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function matchesQuery(record) {
  if (!state.query) return true;
  return JSON.stringify(record).toLowerCase().includes(state.query.toLowerCase());
}

function statusPill(status) {
  if (status === "approved" || status === "safe") return `<span class="pill pill-ok">${status}</span>`;
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
          <div><strong>${item.name}</strong><br>${item.source.importMode} · ${item.source.license}</div>
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
              <h4>${game.name}</h4>
              <div class="meta-row">
                ${(game.game?.platforms || []).map((platform) => `<span class="pill">${platform}</span>`).join("")}
              </div>
            </div>
            ${statusPill(game.safety.reviewStatus)}
          </header>
          <ul class="features">
            ${(game.features || [])
              .map(
                (feature) => `
                  <li>
                    <span>${feature.name}</span>
                    ${statusPill(feature.safetyStatus)}
                  </li>
                `,
              )
              .join("")}
          </ul>
          <div class="meta-row">
            <span class="pill">${game.source.importMode}</span>
            <span class="pill">${game.source.license}</span>
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
          <td>${record.name}</td>
          <td>${record.source.importMode}</td>
          <td>${record.source.license}</td>
          <td>${statusPill(record.safety.reviewStatus)}</td>
          <td><a href="${record.source.url}" target="_blank" rel="noreferrer">${sourceHost(record.source.url)}</a></td>
        </tr>
      `,
    )
    .join("");
}

function renderBuilderSelect() {
  $("#builder-game").innerHTML = registry.games
    .map((game) => `<option value="${game.id}">${game.name}</option>`)
    .join("");
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
  const draft = {
    name: "Local Value Editor",
    gameId,
    gameName: game?.name || gameId,
    offlineOnly: true,
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
          <div><strong>${candidate.address}</strong><br>${candidate.type}</div>
          <span>${candidate.value}</span>
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
  });

  $("#first-scan").addEventListener("click", firstScan);
  $("#narrow-scan").addEventListener("click", narrowScan);
  $("#save-draft").addEventListener("click", saveDraft);
}

bindEvents();
renderAll();
