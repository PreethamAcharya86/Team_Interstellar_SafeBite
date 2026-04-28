/* IngredientIQ - Frontend App Logic */

const API_BASE = "http://localhost:5000"; // relative, same origin as Flask
let riskChartInstance = null;

// ── DOM ──────────────────────────────────────────────────────
const form = document.getElementById("analyzeForm");
const resultsSection = document.getElementById("results");
const loadingOverlay = document.getElementById("loadingOverlay");
const analyzeBtn = document.getElementById("analyzeBtn");
const demoBtn = document.getElementById("demoBtn");
let errorContainer = null;

// Create error message container if not exists
function getOrCreateErrorContainer() {
  if (errorContainer && errorContainer.parentNode) {
    return errorContainer;
  }
  errorContainer = document.createElement("div");
  errorContainer.id = "errorContainer";
  errorContainer.className = "error-container hidden";
  errorContainer.innerHTML = `
    <div class="error-box">
      <div class="error-header">
        <span class="error-icon">⚠️</span>
        <span class="error-title">Error</span>
        <button class="error-close" onclick="closeError()">&times;</button>
      </div>
      <div class="error-message"></div>
      <div class="error-suggestion"></div>
    </div>
  `;
  form.parentNode.insertBefore(errorContainer, form);
  return errorContainer;
}

// ── Sample Products ──────────────────────────────────────────
const SAMPLES = [
  { product_name: "Kurkure Masala Munch", category: "snacks" },
  { product_name: "Frooti Mango Drink", category: "juice" },
  { product_name: "Britannia NutriChoice", category: "biscuits" },
  { product_name: "Paper Boat Aam Panna", category: "juice" },
  { product_name: "Act II Butter Popcorn", category: "snacks" },
  { product_name: "Parle-G Gluco Biscuits", category: "biscuits" },
];

let sampleIndex = 0;

demoBtn.addEventListener("click", () => {
  const sample = SAMPLES[sampleIndex % SAMPLES.length];
  document.getElementById("productName").value = sample.product_name;
  document.getElementById("category").value = sample.category;
  sampleIndex++;
});

// ── Form Submit ──────────────────────────────────────────────
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const productName = document.getElementById("productName").value.trim();
  const category = document.getElementById("category").value;

  // Clear previous errors
  closeError();
  resultsSection.classList.add("hidden");

  // Validation
  if (!productName) {
    showError(
      "Product name is required",
      "Please enter a product name (e.g., Kurkure Masala Munch)",
    );
    return;
  }
  if (!category) {
    showError(
      "Category is required",
      "Please select a category: Snacks, Biscuits, or Juice",
    );
    return;
  }

  showLoading(true);
  analyzeBtn.disabled = true;

  try {
    const response = await fetch(`${API_BASE}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_name: productName, category }),
    });

    const data = await response.json();

    if (!response.ok) {
      const errorMsg = data.error || "Analysis failed";
      const suggestion =
        response.status === 500
          ? "The server encountered an error. Please try again or check that the API key is properly configured."
          : "Try another product name or check your internet connection.";
      showError(errorMsg, suggestion);
      return;
    }

    renderResults(data);
  } catch (err) {
    console.error(err);
    showError(
      "Network error",
      "Could not connect to the server. Make sure the backend is running on http://localhost:5000",
    );
  } finally {
    showLoading(false);
    analyzeBtn.disabled = false;
  }
});

// ── Render Results ───────────────────────────────────────────
function renderResults(data) {
  resultsSection.classList.remove("hidden");

  // Score card
  const scoreNum = document.getElementById("scoreNumber");
  const scoreStars = document.getElementById("scoreStars");
  const scoreBadge = document.getElementById("scoreBadge");
  const scoreProductName = document.getElementById("scoreProductName");

  scoreNum.textContent = data.health_score.toFixed(1);
  scoreNum.className = "score-number " + getColorClass(data.health_score);

  scoreBadge.textContent = data.score_badge || getRatingText(data.health_score);
  scoreBadge.className = "score-badge-el " + getColorClass(data.health_score);

  scoreStars.textContent = getStars(data.health_score);
  scoreProductName.textContent = data.product_name;

  // Risk pills
  const pills = document.getElementById("riskPills");
  const rc = data.risk_counts || {};
  pills.innerHTML = `
    <div class="risk-pill safe">✅ Safe: ${rc.safe || 0}</div>
    <div class="risk-pill low">🟢 Low: ${rc.low || 0}</div>
    <div class="risk-pill medium">🟡 Medium: ${rc.medium || 0}</div>
    <div class="risk-pill high">🔴 High: ${rc.high || 0}</div>
  `;

  // Pie/Bar chart
  renderRiskChart(data.risk_counts || {});

  // Harmful ingredients
  const harmfulSection = document.getElementById("harmfulSection");
  const harmfulList = document.getElementById("harmfulList");
  if (data.harmful_ingredients && data.harmful_ingredients.length > 0) {
    harmfulSection.classList.remove("hidden");
    harmfulList.innerHTML = data.harmful_ingredients
      .map(
        (h) => `
      <div class="harmful-item">
        <div class="risk-dot ${h.risk}"></div>
        <div>
          <div class="item-name">${h.name}</div>
          <div class="item-reason">${h.reason}</div>
        </div>
        <span class="item-badge ${h.risk}">${h.risk}</span>
      </div>
    `,
      )
      .join("");
  } else {
    harmfulSection.classList.remove("hidden");
    harmfulList.innerHTML = `<div class="no-harmful">🎉 No harmful additives detected! This product has a clean ingredient list.</div>`;
  }

  // Allergens
  const allergenSection = document.getElementById("allergenSection");
  const allergenList = document.getElementById("allergenList");
  allergenSection.classList.remove("hidden");
  if (data.allergens && data.allergens.length > 0) {
    const icons = {
      "milk/dairy": "🥛",
      "tree nuts": "🌰",
      peanuts: "🥜",
      "gluten/wheat": "🌾",
      soy: "🫘",
      eggs: "🥚",
      sesame: "🌿",
      sulphites: "⚗️",
      mustard: "🟡",
      fish: "🐟",
    };
    allergenList.innerHTML = data.allergens
      .map(
        (a) => `
      <div class="allergen-tag">${icons[a] || "⚠️"} ${a.replace("/", " / ").toUpperCase()}</div>
    `,
      )
      .join("");
  } else {
    allergenList.innerHTML = `<div class="no-allergen">✅ No common allergens detected in ingredient list.</div>`;
  }

  // Ingredient bars
  const barsContainer = document.getElementById("ingredientBars");
  if (data.ingredient_risks && data.ingredient_risks.length > 0) {
    const riskWidths = { safe: 20, low: 45, medium: 72, high: 100 };
    barsContainer.innerHTML = data.ingredient_risks
      .slice(0, 18)
      .map(
        (ing) => `
      <div class="ing-bar-row">
        <div class="ing-bar-name" title="${ing.name}">${ing.name}</div>
        <div class="ing-bar-track">
          <div class="ing-bar-fill ${ing.risk}" style="width: ${riskWidths[ing.risk] || 20}%"></div>
        </div>
        <div class="ing-bar-label ${ing.risk}">${ing.risk}</div>
      </div>
    `,
      )
      .join("");
  }

  // Alternatives
  const altSection = document.getElementById("alternativesSection");
  const altList = document.getElementById("alternativesList");
  const altIcons = { snacks: "🍿", biscuits: "🍪", juice: "🥤" };
  const icon = altIcons[data.category] || "🌿";
  if (data.alternatives && data.alternatives.length > 0) {
    altSection.classList.remove("hidden");
    altList.innerHTML = data.alternatives
      .map(
        (a) => `
      <div class="alt-card">
        <div class="alt-icon">${icon}</div>
        <div class="alt-name">${a.name}</div>
        <div class="alt-brand">${a.brand || ""}</div>
        <div class="alt-reason">${a.reason}</div>
      </div>
    `,
      )
      .join("");
  } else {
    altSection.classList.add("hidden");
  }

  // Model note
  const ingredientsSource = data.ingredients_source || "Unknown";
  const alternativesSource = data.alternatives_source || "Rule-based";
  document.getElementById("modelNote").textContent =
    `Ingredients: ${ingredientsSource} | Alternatives: ${alternativesSource} | Analysis: ${data.model_used || "Rule-based engine"}`;

  // Scroll to results
  setTimeout(() => {
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }, 100);
}

// ── Risk Chart ────────────────────────────────────────────────
function renderRiskChart(risk_counts) {
  const ctx = document.getElementById("riskChart").getContext("2d");

  if (riskChartInstance) {
    riskChartInstance.destroy();
  }

  const safe = (risk_counts.safe || 0) + (risk_counts.low || 0);
  const medium = risk_counts.medium || 0;
  const high = risk_counts.high || 0;

  riskChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Safe / Low Risk", "Medium Risk", "High Risk"],
      datasets: [
        {
          data: [safe, medium, high],
          backgroundColor: ["#43A047", "#FFA726", "#EF5350"],
          borderColor: ["#2E7D32", "#E65100", "#C62828"],
          borderWidth: 1.5,
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.raw} ingredient${ctx.raw !== 1 ? "s" : ""}`,
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { stepSize: 1, font: { family: "'DM Sans'" } },
          grid: { color: "#F0EDE8" },
        },
        x: {
          ticks: { font: { family: "'DM Sans'", size: 12 } },
          grid: { display: false },
        },
      },
    },
  });
}

// ── Helpers ───────────────────────────────────────────────────
function getColorClass(score) {
  if (score >= 4.0) return "green";
  if (score >= 2.5) return "amber";
  return "red";
}

function getStars(score) {
  const full = Math.round(score);
  const empty = 5 - full;
  return "★".repeat(full) + "☆".repeat(empty);
}

function getRatingText(score) {
  if (score >= 4.5) return "🟢 Excellent";
  if (score >= 3.5) return "🟢 Good";
  if (score >= 2.5) return "🟡 Moderate";
  if (score >= 1.5) return "🟠 Concerning";
  return "🔴 Poor";
}

function showLoading(show) {
  loadingOverlay.classList.toggle("hidden", !show);
}

// ── Error Handling ────────────────────────────────────────────
function showError(message, suggestion = "") {
  const container = getOrCreateErrorContainer();
  container.querySelector(".error-message").textContent = message;

  const suggestionEl = container.querySelector(".error-suggestion");
  if (suggestion) {
    suggestionEl.textContent = suggestion;
    suggestionEl.classList.remove("hidden");
  } else {
    suggestionEl.classList.add("hidden");
  }

  container.classList.remove("hidden");

  // Scroll to error
  setTimeout(() => {
    container.scrollIntoView({ behavior: "smooth", block: "start" });
  }, 100);
}

function closeError() {
  const container = getOrCreateErrorContainer();
  container.classList.add("hidden");
}
