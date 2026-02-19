document.addEventListener("DOMContentLoaded", () => {

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
