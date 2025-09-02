document.addEventListener("DOMContentLoaded", function () {
    const params = new URLSearchParams(window.location.search);
    const section = params.get("section") || "cyber-cell"; // default

    // Hide all content-sections
    document.querySelectorAll(".content-section").forEach(el => el.classList.remove("active"));

    // Show the selected section
    const activeSection = document.getElementById(section + "-content");
    if (activeSection) {
        activeSection.classList.add("active");
    }

    // Highlight sidebar nav
    document.querySelectorAll(".nav-link1").forEach(el => el.classList.remove("active"));
    const activeNav = document.querySelector(`.nav-link1[data-section="${section}"]`);
    if (activeNav) {
        activeNav.classList.add("active");
    }
});

