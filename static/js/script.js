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

// bar chart for interested percentage by alert
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

// 100% stacked bar chart for open vs closed postings by alert
const closedChart = document.getElementById("alertClosedChart");

if (closedChart && window.closedStats) {

    const closedLabels = window.closedStats.map(
        closed => closed.alert_name
    );

    const closedRates = window.closedStats.map(
        closed => closed.closed_rate
    );

    const openRates = window.closedStats.map(
        closed => 100 - closed.closed_rate
    );

    const closedJobs = window.closedStats.map(
        closed => closed.closed_jobs
    );

    const reviewedJobs = window.closedStats.map(
        closed => closed.reviewed_jobs
    );

    const openJobs = window.closedStats.map(
        closed => closed.reviewed_jobs - closed.closed_jobs
    );

    new Chart(closedChart, {
        type: "bar",

        data: {
            labels: closedLabels,

            datasets: [
                {
                    label: "Open",
                    data: openRates
                },
                {
                    label: "Closed",
                    data: closedRates
                }
            ]
        },

        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,

            scales: {
                x: {
                    stacked: true,
                    beginAtZero: true,
                    max: 100,

                    grid: {
                        display: false
                    },

                    ticks: {
                        callback: function(value) {
                            return value + "%";
                        }
                    }
                },

                y: {
                    stacked: true
                }
            },

            plugins: {
                legend: {
                    display: true
                },

                datalabels: {
                    formatter: function(value) {
                        return value.toFixed(1) + "%";
                    }
                },

                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const index = context.dataIndex;

                            if (context.dataset.label === "Closed") {
                                return [
                                    "Closed Rate: " + closedRates[index] + "%",
                                    "Closed Jobs: " + closedJobs[index],
                                    "Reviewed Jobs: " + reviewedJobs[index]
                                ];
                            }

                            return [
                                "Open Rate: " + openRates[index].toFixed(1) + "%",
                                "Open Jobs: " + openJobs[index],
                                "Reviewed Jobs: " + reviewedJobs[index]
                            ];
                        }
                    }
                }
            }
        }
    });
}

// line chart for reviewed jobs by week
const jobsByWeekChart = document.getElementById("jobsByWeekChart");

if (jobsByWeekChart && window.jobsByWeek) {

    const weekLabels = window.jobsByWeek.map(row => {
        const date = new Date(row.week_start + "T00:00:00");

        return date.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric"
        });
    });

    const reviewedJobs = window.jobsByWeek.map(
        row => row.reviewed_jobs
    );

    new Chart(jobsByWeekChart, {
        type: "line",

        data: {
            labels: weekLabels,

            datasets: [{
                label: "Reviewed Jobs",
                data: reviewedJobs,
                tension: 0.25,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,

            scales: {
                y: {
                    beginAtZero: true,

                    ticks: {
                        precision: 0
                    }
                },

                x: {
                    grid: {
                        display: false
                    }
                }
            },

            plugins: {
                legend: {
                    display: false
                },

                datalabels: {
                    anchor: "end",
                    align: "top",

                    formatter: function(value) {
                        return value;
                    }
                },

                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return "Week of " + context[0].label;
                        },

                        label: function(context) {
                            return context.raw + " reviewed jobs";
                        }
                    }
                }
            }
        }
    });
}
