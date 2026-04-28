// ── Scroll Animation Handler ─────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    // Initialize scroll animations
    initializeScrollAnimations();

    // Initialize risk chart if on index page
    initializeRiskChart();

    // Initialize risk breakdown comparison if on compare page
    initializeRiskComparison();
});

// Intersection Observer for scroll animations
function initializeScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px",
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                const element = entry.target;

                // Add staggered delay for multiple elements
                const index = Array.from(
                    element.parentElement?.children || [element]
                ).indexOf(element);
                const delay = index * 0.1;

                element.style.animationDelay = `${delay}s`;
                element.classList.remove(
                    "scroll-animate",
                    "scroll-animate-left",
                    "scroll-animate-right",
                    "scroll-animate-scale"
                );

                // Trigger animation by re-adding class
                void element.offsetWidth; // Trigger reflow
                element.classList.add(element.dataset.animation || "scroll-animate");

                observer.unobserve(element);
            }
        });
    }, observerOptions);

    // Apply observer to all cards and section cards
    document.querySelectorAll(".card, .section-card").forEach((element) => {
        element.classList.add(element.dataset.animation || "scroll-animate");
        observer.observe(element);
    });
}

// Initialize risk chart on index page
function initializeRiskChart() {
    const riskChartCanvas = document.getElementById("riskChart");

    if (riskChartCanvas) {
        const ctx = riskChartCanvas.getContext("2d");

        // Example data for the risk breakdown
        const data = {
            labels: ["High Risk", "Moderate Risk", "Low Risk"],
            datasets: [
                {
                    label: "Ingredient Risk Breakdown",
                    data: [30, 50, 20], // Example values
                    backgroundColor: ["#c62828", "#f57f17", "#2e7d32"],
                    borderRadius: 8,
                },
            ],
        };

        const options = {
            indexAxis: "y",
            responsive: true,
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return `${context.raw}%`;
                        },
                    },
                },
            },
            animation: {
                duration: 1500,
                easing: "easeInOutQuart",
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                },
            },
        };

        // Render the chart
        new Chart(ctx, {
            type: "barh",
            data: data,
            options: options,
        });
    }
}

// Initialize risk breakdown comparison on compare page
function initializeRiskComparison() {
    const riskComparisonDiv = document.getElementById("riskComparison");

    if (riskComparisonDiv && typeof Chart !== "undefined") {
        // This will be populated after the comparison is fetched
        // We need to add a global function to handle chart creation after data is loaded
        window.createRiskComparisonCharts = createRiskComparisonCharts;
    }
}

// Create risk breakdown comparison charts
function createRiskComparisonCharts(product1Data, product2Data) {
    const riskComparisonDiv = document.getElementById("riskComparison");

    if (!riskComparisonDiv) return;

    // Clear previous content
    riskComparisonDiv.innerHTML = "";

    // Create container for two charts
    const chartsContainer = document.createElement("div");
    chartsContainer.style.display = "grid";
    chartsContainer.style.gridTemplateColumns = "1fr 1fr";
    chartsContainer.style.gap = "20px";
    chartsContainer.style.marginTop = "20px";

    // Chart 1
    const canvas1 = document.createElement("canvas");
    canvas1.id = "riskChart1";
    canvas1.height = 300;

    const container1 = document.createElement("div");
    container1.style.position = "relative";
    container1.appendChild(canvas1);

    // Chart 2
    const canvas2 = document.createElement("canvas");
    canvas2.id = "riskChart2";
    canvas2.height = 300;

    const container2 = document.createElement("div");
    container2.style.position = "relative";
    container2.appendChild(canvas2);

    chartsContainer.appendChild(container1);
    chartsContainer.appendChild(container2);
    riskComparisonDiv.appendChild(chartsContainer);

    // Create charts with animation
    setTimeout(() => {
        createBarChart(
            "riskChart1",
            product1Data.product_name || "Product 1",
            product1Data
        );
        createBarChart(
            "riskChart2",
            product2Data.product_name || "Product 2",
            product2Data
        );
    }, 100);
}

// Helper function to create bar charts for comparison
function createBarChart(canvasId, title, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    const riskData = {
        highRisk: data.harmful_count || 0,
        moderateRisk: data.allergen_count || 0,
        lowRisk: Math.max(
            0,
            (data.ingredient_count || 10) -
            (data.harmful_count || 0) -
            (data.allergen_count || 0)
        ),
    };

    const chartData = {
        labels: ["High Risk", "Moderate Risk", "Low Risk"],
        datasets: [
            {
                label: title,
                data: [
                    riskData.highRisk,
                    riskData.moderateRisk,
                    riskData.lowRisk,
                ],
                backgroundColor: ["#c62828", "#f57f17", "#2e7d32"],
                borderRadius: 8,
                borderWidth: 0,
            },
        ],
    };

    const chartOptions = {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false,
            },
            tooltip: {
                backgroundColor: "rgba(0, 0, 0, 0.8)",
                padding: 10,
                titleFont: { size: 12 },
                bodyFont: { size: 12 },
            },
        },
        animation: {
            duration: 1500,
            easing: "easeInOutQuart",
        },
        scales: {
            x: {
                beginAtZero: true,
            },
        },
    };

    new Chart(ctx, {
        type: "barh",
        data: chartData,
        options: chartOptions,
    });
}

// Export functions for use in other scripts
window.createRiskComparisonCharts = createRiskComparisonCharts;
