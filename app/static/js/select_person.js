let selectedRow = null;

async function loadPerson(iin, row) {
    if (selectedRow) {
        selectedRow.classList.remove("bg-accent-content");
    }

    row.classList.add("bg-accent-content");
    selectedRow = row;

    const response = await fetch(`/reports/person/${iin}`);
    const data = await response.json();

    const container = document.getElementById("person-details");

    if (!data) {
        container.innerHTML = "<p class='text-error'>Данные не найдены</p>";
    } else {
        container.innerHTML = `
            <h3 class="text-lg text-accent font-bold mb-2">Данные физ.лица</h3>
            <div class="flex gap-1 text-base-content"><b>ИИН:</b> <p class="select-all">${data.iin}</p></div>
            <div class="flex gap-1 text-base-content"><b>ФИО:</b> <p class="select-all">${data.lastname || ''} ${data.firstname || ''} ${data.middlename || ''}</p></div>
            <div class="flex gap-1 text-base-content"><b>Дата рождения:</b> <p class="select-all">${data.birthdate || ''}</p></div>
            <div class="flex gap-1 text-base-content"><b>Адрес:</b> <p class="select-all">${data.address || ''}</p></div>
        `;
    }

    container.classList.remove("hidden");
}