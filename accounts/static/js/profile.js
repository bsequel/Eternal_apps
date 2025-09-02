const toggleBtn = document.getElementById("profileToggle");
const dropdown = document.getElementById("profileDropdown");
const profileWrapper = document.getElementById("profileWrapper");

let isClickedOpen = false; // track click state

// Hover behavior (only works if not clicked open)
profileWrapper.addEventListener("mouseenter", () => {
    if (!isClickedOpen) dropdown.classList.add("active");
});

profileWrapper.addEventListener("mouseleave", () => {
    if (!isClickedOpen) dropdown.classList.remove("active");
});

// Click to toggle dropdown (like Google)
toggleBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    isClickedOpen = !isClickedOpen;
    dropdown.classList.toggle("active", isClickedOpen);
});

// Close when clicking outside
document.addEventListener("click", (e) => {
    if (!profileWrapper.contains(e.target)) {
        isClickedOpen = false;
        dropdown.classList.remove("active");
    }
});