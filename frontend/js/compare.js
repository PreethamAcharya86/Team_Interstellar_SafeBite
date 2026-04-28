// 📊 Risk Breakdown Comparison Logic

document.addEventListener("DOMContentLoaded", () => {
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
                    backgroundColor: ["#ff4d4d", "#ffc107", "#28a745"],
                },
            ],
        };

        const options = {
            responsive: true,
            plugins: {
                legend: {
                    position: "top",
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return `${context.label}: ${context.raw}%`;
                        },
                    },
                },
            },
        };

        // Render the chart
        new Chart(ctx, {
            type: "doughnut",
            data: data,
            options: options,
        });
    }
});