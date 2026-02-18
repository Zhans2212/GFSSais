const toggleBtn = document.getElementById("theme-toggle");
const sunIcon = document.getElementById("sun-icon");
const moonIcon = document.getElementById("moon-icon");

function updateIcons(theme) {
  if (theme === "dark") {
    sunIcon.classList.add("hidden");
    moonIcon.classList.remove("hidden");
  } else {
    moonIcon.classList.add("hidden");
    sunIcon.classList.remove("hidden");
  }
}

function setTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("theme", theme);
  updateIcons(theme);
}

function toggleTheme() {
  const currentTheme =
    document.documentElement.getAttribute("data-theme");
  const newTheme = currentTheme === "dark" ? "bumblebee" : "dark";
  setTheme(newTheme);
}

toggleBtn.addEventListener("click", toggleTheme);

// при загрузке
const savedTheme = localStorage.getItem("theme") || "bumblebee";
setTheme(savedTheme);
