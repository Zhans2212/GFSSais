function loginForm() {
return {
  username: "",
  password: "",
  loading: false,
  error: "",

  async submit() {
    this.error = "";
    this.loading = true;

    try {
      const response = await fetch("/login/auth", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({
          username: this.username,
          password: this.password
        })
      });

      if (response.ok) {
        window.location.href = "/reports";
        return;
      }

      if (response.status === 401) {
        this.error = "Неверный логин или пароль";
      } else {
        this.error = "Ошибка входа";
      }
    } catch (e) {
      this.error = "Сеть недоступна или сервер не отвечает";
    } finally {
      this.loading = false;
    }
  }
};
}