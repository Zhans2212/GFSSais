function updateTotals() {
    let totalSum = 0;
    let totalRefund = 0;
    let count = 0;

    const rows = document.querySelectorAll("tbody tr");
    rows.forEach(row => {
        const style = getComputedStyle(row).display;
        if (style !== "none") {  // только видимые строки
            const sumCell = row.cells[5].innerText.replace(/,/g, '');
            const refundCell = row.cells[6].innerText.replace(/,/g, '');
            totalSum += parseFloat(sumCell) || 0;
            totalRefund += parseFloat(refundCell) || 0;
            count += 1;
        }
    });

    document.getElementById("totals").innerText =
        `Сумма платежа: ${totalSum.toFixed(2)} | ` +
        `Сумма возврата: ${totalRefund.toFixed(2)} | ` +
        `Кол-во записей: ${count}`;
}

window.addEventListener("DOMContentLoaded", updateTotals);

document.getElementById("select-status").addEventListener("change", function() {
    let value = this.value;
    const rows = document.querySelectorAll("tbody tr");

    rows.forEach(row => {
        const statusCell = row.cells[7].innerText.trim();
        if (value === "Все записи" || value === "all") {
            row.style.display = "";
        } else {
            row.style.display = (statusCell === value.split(' ')[0]) ? "" : "none";
        }
    });

    updateTotals();  // пересчёт после фильтрации
});