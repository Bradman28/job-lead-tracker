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
