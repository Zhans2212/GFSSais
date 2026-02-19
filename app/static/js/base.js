document.addEventListener("DOMContentLoaded", () => {
    // Кнопка отчетов
    const reportsBtn = document.getElementById("reports-button");
    if (reportsBtn) {
        reportsBtn.addEventListener("click", async (e) => {
            e.preventDefault();

            const response = await fetch("/reports", {
                method: "GET"
            });
            if (response.ok) {
                window.location.href = "/reports";
            } else {
                alert("Ошибка!");
            }
        });
    }

    // Кнопка профиля
    const profileBtn = document.getElementById("profile-button");
    if (profileBtn) {
        profileBtn.addEventListener("click", () => {
            window.location.href = "/profile";
        });
    }

    // Кнопка выхода
    const exitBtn = document.getElementById("exit-button");
    if (exitBtn) {
        exitBtn.addEventListener("click", async (e) => {
            e.preventDefault();

            const response = await fetch("/login/logout", {
                method: "POST"
            });

            if (response.ok) {
                window.location.href = "/login";
            } else {
                alert("Ошибка!");
            }
        });
    }

});
