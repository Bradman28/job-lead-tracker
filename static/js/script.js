window.addEventListener("beforeunload", function (){
    sessionStorage.setItem("scrollPosition", window.scrollY);
});

window.addEventListener("load", function () {
    const paginationClicked = sessionStorage.getItem("paginationClicked");
    const scrollPosition = sessionStorage.getItem("scrollPosition");

    if (paginationClicked === "true") {
        window.scrollTo(0, 0);
        sessionStorage.removeItem("paginationClicked");
        sessionStorage.removeItem("scrollPosition");
    } else if (scrollPosition !== null) {
        window.scrollTo(0, parseInt(scrollPosition));
    }
});

const selectAllCheckbox = document.getElementById("select-all");
const jobCheckboxes = document.querySelectorAll(".job-checkbox");

if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener("change", function () {
        jobCheckboxes.forEach(function (checkbox) {
            checkbox.checked = selectAllCheckbox.checked;
        });
    });
}

document.querySelectorAll(".job-link").forEach(link => {

    link.addEventListener("click", function() {

        localStorage.setItem(
            "lastViewedJobId",
            this.dataset.jobId
        );

        // remove previous highlight
        document.querySelectorAll(".last-viewed").forEach(row => {
            row.classList.remove("last-viewed");
        });

        //highlight clicked row
        const row = document.getElementById("job-" + this.dataset.jobId);

        if (row) {
            row.classList.add("last-viewed");
        }
    });
});

const lastViewed = localStorage.getItem("lastViewedJobId");
const row = document.getElementById(
    "job-" + lastViewed
);

if (row) {
    row.classList.add("last-viewed");

    row.scrollIntoView({
        behavior: "smooth",
        block: "center"
});
}

document.querySelectorAll(".page-link").forEach(link => {
    link.addEventListener("click", function () {
        sessionStorage.setItem("paginationClicked", "true")
    });
});

const alertChart = document.getElementById("alertInterestChart");

if (alertChart && window.alertStats) {

    Chart.register(ChartDataLabels);

    const alertLabels = window.alertStats.map(
        alert => alert.alert_name
    );

    const alertRates = window.alertStats.map(
        alert => alert.interested_rate
    );

    const alertInterested = window.alertStats.map(
        alert => alert.interested_jobs
    );

    const alertReviewed = window.alertStats.map(
        alert => alert.reviewed_jobs
    );

    new Chart(alertChart, {
        type: "bar",

        data: {
            labels: alertLabels,

            datasets: [{
                label: "Interest Rate",
                data: alertRates
            }]
        },

        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,

            scales: {
                x: {
                    beginAtZero: true,
                    suggestedMax: 30,

                    grid: {
                        display: false
                    },

                    ticks: {
                        callback: function(value) {
                            return value + "%";
                        }
                    }
                }
            },

            plugins: {
                legend: {
                    display: false
                },

                datalabels: {
                    anchor: "end",
                    align: "end",

                    formatter: function(value) {
                        return value + "%";
                    }
                },

                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;

                            return [
                                "Interest Rate: " + alertRates[index] + "%",
                                "Interested Jobs: " + alertInterested[index],
                                "Reviewed Jobs: " + alertReviewed[index]
                            ];
                        }
                    }
                }
            }
        }
    });
}
