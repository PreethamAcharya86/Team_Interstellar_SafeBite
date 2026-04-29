/* SafeBite - Product Comparison Logic */

const API_BASE = "http://localhost:5000"; // relative, same origin as Flask
let errorContainer = null;

// ── Sample Products for Demo ──────────────────────────────
const SAMPLE_COMPARISONS = [
  {
    product1: { product_name: "Kurkure Masala Munch", category: "snacks" },
    product2: { product_name: "Britannia NutriChoice", category: "biscuits" },
  },
  {
    product1: { product_name: "Frooti Mango Drink", category: "juice" },
    product2: { product_name: "Paper Boat Aam Panna", category: "juice" },
  },
  {
    product1: { product_name: "Act II Butter Popcorn", category: "snacks" },
    product2: { product_name: "Parle-G Gluco Biscuits", category: "biscuits" },
  },
];

let sampleIndex = 0;

// ── DOM Elements ──────────────────────────────────────────
const compareForm = document.getElementById("compareForm");
const comparisonResults = document.getElementById("comparisonResults");
const loadingOverlay = document.getElementById("loadingOverlay");
const compareBtn = document.getElementById("compareBtn");
const compareDemoBtn = document.getElementById("compareDemoBtn");

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
  compareForm.parentNode.insertBefore(errorContainer, compareForm);
  return errorContainer;
}

// Show error message
function showError(message, suggestion = "") {
  const container = getOrCreateErrorContainer();
  container.querySelector(".error-message").textContent = message;
  container.querySelector(".error-suggestion").textContent = suggestion;
  container.classList.remove("hidden");
}

// Close error message
function closeError() {
  const container = getOrCreateErrorContainer();
  container.classList.add("hidden");
}

// Show/hide loading overlay
function showLoading(show) {
  if (show) {
    loadingOverlay.classList.remove("hidden");
  } else {
    loadingOverlay.classList.add("hidden");
  }
}

// ── Demo Button ──────────────────────────────────────────
compareDemoBtn.addEventListener("click", () => {
  const sample = SAMPLE_COMPARISONS[sampleIndex % SAMPLE_COMPARISONS.length];
  document.getElementById("product1Name").value = sample.product1.product_name;
  document.getElementById("category1").value = sample.product1.category;
  document.getElementById("product2Name").value = sample.product2.product_name;
  document.getElementById("category2").value = sample.product2.category;
  sampleIndex++;
});

// ── Form Submit ──────────────────────────────────────────
compareForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const product1Name = document.getElementById("product1Name").value.trim();
  const category1 = document.getElementById("category1").value;
  const product2Name = document.getElementById("product2Name").value.trim();
  const category2 = document.getElementById("category2").value;

  // Clear previous errors
  closeError();
  comparisonResults.classList.add("hidden");

  // Validation
  if (!product1Name) {
    showError(
      "Product 1 name is required",
      "Please enter the first product name",
    );
    return;
  }
  if (!category1) {
    showError("Category 1 is required", "Please select category for product 1");
    return;
  }
  if (!product2Name) {
    showError(
      "Product 2 name is required",
      "Please enter the second product name",
    );
    return;
  }
  if (!category2) {
    showError("Category 2 is required", "Please select category for product 2");
    return;
  }

  if (product1Name.toLowerCase() === product2Name.toLowerCase()) {
    showError(
      "Products must be different",
      "Please enter two different product names to compare",
    );
    return;
  }

  showLoading(true);
  compareBtn.disabled = true;

  try {
    const response = await fetch(`${API_BASE}/api/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_1: { product_name: product1Name, category: category1 },
        product_2: { product_name: product2Name, category: category2 },
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      const errorMsg = data.error || "Comparison failed";
      const suggestion =
        response.status === 500
          ? "The server encountered an error. Please try again."
          : "Try different product names or check your internet connection.";
      showError(errorMsg, suggestion);
      return;
    }

    renderComparison(data);
  } catch (err) {
    console.error(err);
    showError(
      "Network error",
      "Could not connect to the server. Make sure the backend is running.",
    );
  } finally {
    showLoading(false);
    compareBtn.disabled = false;
  }
});

// ── Render Comparison Results ────────────────────────────
function renderComparison(data) {
  comparisonResults.classList.remove("hidden");

  const product1 = data.product_1;
  const product2 = data.product_2;
  const winner = data.winner;

  // Set table header product names
  document.getElementById("table-product1").textContent = product1.product_name;
  document.getElementById("table-product2").textContent = product2.product_name;

  // Render winner section
  renderWinner(winner, product1, product2);

  // Render score cards
  renderScoreCards(product1, product2);

  // Render harmful ingredients comparison
  renderHarmfulComparison(product1, product2);

  // Render allergen comparison
  renderAllergenComparison(product1, product2);

  // Render score table
  renderScoreTable(product1, product2, winner);

  // Render recommendation
  renderRecommendation(winner, product1, product2);

  // Scroll to results
  setTimeout(() => {
    comparisonResults.scrollIntoView({ behavior: "smooth", block: "start" });
  }, 100);
}

// Render winner section
function renderWinner(winner, product1, product2) {
  const winnerSection = document.getElementById("winnerSection");
  const winnerName =
    winner === "product_1" ? product1.product_name : product2.product_name;
  const winnerScore =
    winner === "product_1" ? product1.health_score : product2.health_score;
  const loserScore =
    winner === "product_1" ? product2.health_score : product1.health_score;
  const difference = (winnerScore - loserScore).toFixed(1);

  const badgeClass = getColorClass(winnerScore);
  const trophyEmoji = winnerScore >= 4 ? "🏆" : winnerScore >= 3 ? "🥇" : "👍";

  winnerSection.innerHTML = `
    <div class="winner-card ${badgeClass}">
      <div class="winner-badge">${trophyEmoji} WINNER</div>
      <div class="winner-name">${winnerName}</div>
      <div class="winner-score">${winnerScore.toFixed(1)}/5.0</div>
      <div class="winner-margin">Better by ${difference} points</div>
    </div>
  `;
}

// Render score cards
function renderScoreCards(product1, product2) {
  const product1Card = document.getElementById("product1Card");
  const product2Card = document.getElementById("product2Card");

  product1Card.innerHTML = renderScoreCard(product1);
  product2Card.innerHTML = renderScoreCard(product2);
}

function renderScoreCard(product) {
  const colorClass = getColorClass(product.health_score);
  const rc = product.risk_counts || {};
  const stars = getStars(product.health_score);
  const badge = product.score_badge || getRatingText(product.health_score);

  return `
    <div class="score-card-compare ${colorClass}">
      <div class="score-header">
        <div class="score-product">${product.product_name}</div>
        <div class="score-category">${product.category}</div>
      </div>
      <div class="score-display">
        <div class="score-number">${product.health_score.toFixed(1)}</div>
        <div class="score-max">/ 5.0</div>
      </div>
      <div class="score-stars">${stars}</div>
      <div class="score-badge ${colorClass}">${badge}</div>
      <div class="risk-summary-pills">
        <div class="pill safe">✅ ${rc.safe || 0}</div>
        <div class="pill low">🟢 ${rc.low || 0}</div>
        <div class="pill medium">🟡 ${rc.medium || 0}</div>
        <div class="pill high">🔴 ${rc.high || 0}</div>
      </div>
      <div class="harmful-count">🚨 Harmful: ${product.harmful_count || 0}</div>
    </div>
  `;
}

// Render harmful ingredients comparison
function renderHarmfulComparison(product1, product2) {
  const harmfulComparison = document.getElementById("harmfulComparison");
  const harmful1 = product1.harmful_ingredients || [];
  const harmful2 = product2.harmful_ingredients || [];

  if (harmful1.length === 0 && harmful2.length === 0) {
    harmfulComparison.innerHTML = `
      <div class="no-harmful">🎉 Both products have clean ingredient lists! No harmful additives detected.</div>
    `;
    return;
  }

  let html = '<div class="harmful-comparison-grid">';

  // Product 1
  html += '<div class="harmful-col">';
  html += `<h4>${product1.product_name}</h4>`;
  if (harmful1.length === 0) {
    html += '<div class="no-harmful-small">✅ No harmful ingredients</div>';
  } else {
    html += harmful1
      .map(
        (h) => `
      <div class="harmful-item">
        <div class="risk-dot ${h.risk}"></div>
        <div class="item-details">
          <div class="item-name">${h.name}</div>
          <div class="item-reason">${h.reason}</div>
        </div>
        <span class="item-badge ${h.risk}">${h.risk}</span>
      </div>
    `,
      )
      .join("");
  }
  html += "</div>";

  // Product 2
  html += '<div class="harmful-col">';
  html += `<h4>${product2.product_name}</h4>`;
  if (harmful2.length === 0) {
    html += '<div class="no-harmful-small">✅ No harmful ingredients</div>';
  } else {
    html += harmful2
      .map(
        (h) => `
      <div class="harmful-item">
        <div class="risk-dot ${h.risk}"></div>
        <div class="item-details">
          <div class="item-name">${h.name}</div>
          <div class="item-reason">${h.reason}</div>
        </div>
        <span class="item-badge ${h.risk}">${h.risk}</span>
      </div>
    `,
      )
      .join("");
  }
  html += "</div>";

  html += "</div>";
  harmfulComparison.innerHTML = html;
}

// Render allergen comparison
function renderAllergenComparison(product1, product2) {
  const allergenComparison = document.getElementById("allergenComparison");
  const allergens1 = product1.allergens || [];
  const allergens2 = product2.allergens || [];

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

  let html = '<div class="allergen-comparison-grid">';

  // Product 1
  html += '<div class="allergen-col">';
  html += `<h4>${product1.product_name}</h4>`;
  if (allergens1.length === 0) {
    html += '<div class="no-allergen">✅ No allergens detected</div>';
  } else {
    html += allergens1
      .map(
        (a) => `
      <div class="allergen-tag">${icons[a] || "⚠️"} ${a.replace("/", " / ").toUpperCase()}</div>
    `,
      )
      .join("");
  }
  html += "</div>";

  // Product 2
  html += '<div class="allergen-col">';
  html += `<h4>${product2.product_name}</h4>`;
  if (allergens2.length === 0) {
    html += '<div class="no-allergen">✅ No allergens detected</div>';
  } else {
    html += allergens2
      .map(
        (a) => `
      <div class="allergen-tag">${icons[a] || "⚠️"} ${a.replace("/", " / ").toUpperCase()}</div>
    `,
      )
      .join("");
  }
  html += "</div>";

  html += "</div>";
  allergenComparison.innerHTML = html;
}

// Render score comparison table
function renderScoreTable(product1, product2, winner) {
  const tbody = document.getElementById("scoreTableBody");

  const metrics = [
    {
      label: "Health Score",
      v1: product1.health_score,
      v2: product2.health_score,
      format: (v) => v.toFixed(1),
    },
    {
      label: "Harmful Ingredients",
      v1: product1.harmful_count || 0,
      v2: product2.harmful_count || 0,
      format: (v) => v,
      lowerIsBetter: true,
    },
    {
      label: "Total Ingredients",
      v1: product1.total_ingredients || 0,
      v2: product2.total_ingredients || 0,
      format: (v) => v,
      neutral: true,
    },
    {
      label: "Allergens",
      v1: (product1.allergens || []).length,
      v2: (product2.allergens || []).length,
      format: (v) => v,
      lowerIsBetter: true,
    },
  ];

  tbody.innerHTML = metrics
    .map((metric) => {
      let winnerIcon = "➖";
      if (!metric.neutral) {
        if (metric.lowerIsBetter) {
          winnerIcon =
            metric.v1 < metric.v2 ? "🏆" : metric.v1 > metric.v2 ? "📉" : "➖";
        } else {
          winnerIcon =
            metric.v1 > metric.v2 ? "🏆" : metric.v1 < metric.v2 ? "📉" : "➖";
        }
      }

      return `
        <tr>
          <td class="metric-label">${metric.label}</td>
          <td class="metric-value">${metric.format(metric.v1)}</td>
          <td class="metric-value">${metric.format(metric.v2)}</td>
          <td class="metric-winner">${winnerIcon}</td>
        </tr>
      `;
    })
    .join("");
}

// Render recommendation
function renderRecommendation(winner, product1, product2) {
  const recommendationText = document.getElementById("recommendationText");
  const winnerProduct = winner === "product_1" ? product1 : product2;
  const loserProduct = winner === "product_1" ? product2 : product1;
  const difference = (
    winnerProduct.health_score - loserProduct.health_score
  ).toFixed(1);

  let recommendation = "";

  if (difference >= 2) {
    recommendation = `<strong>${winnerProduct.product_name}</strong> is significantly healthier with a score of ${winnerProduct.health_score.toFixed(1)}/5.0 compared to ${loserProduct.product_name} (${loserProduct.health_score.toFixed(1)}/5.0). <br><br> It has fewer harmful ingredients and a cleaner ingredient profile. <strong>We recommend choosing ${winnerProduct.product_name}.</strong>`;
  } else if (difference >= 1) {
    recommendation = `<strong>${winnerProduct.product_name}</strong> is noticeably healthier than ${loserProduct.product_name}. While both have acceptable ingredient lists, ${winnerProduct.product_name} scores ${difference} points higher. <br><br> <strong>We recommend ${winnerProduct.product_name}</strong> for better health outcomes.`;
  } else {
    recommendation = `Both products are relatively similar in terms of health scores, with ${winnerProduct.product_name} having a slight edge (${difference} points higher). <br><br> Your choice between these two depends on personal preferences, allergies, and taste. Both are acceptable options, but <strong>${winnerProduct.product_name}</strong> is marginally better.`;
  }

  recommendationText.innerHTML = recommendation;
}

// ── Utility Functions ────────────────────────────────────
function getColorClass(score) {
  if (score >= 4) return "excellent";
  if (score >= 3) return "good";
  if (score >= 2) return "fair";
  return "poor";
}

function getStars(score) {
  const fullStars = Math.floor(score);
  const hasHalf = score % 1 >= 0.5;
  let stars = "⭐".repeat(fullStars);
  if (hasHalf) stars += "✨";
  return stars;
}

function getRatingText(score) {
  if (score >= 4.5) return "Excellent 🌟";
  if (score >= 4) return "Very Good ✨";
  if (score >= 3) return "Good 👍";
  if (score >= 2) return "Fair ⚠️";
  return "Poor ⛔";
}
