function getReport() {
return {
    date: null,
    init() {
        const today = new Date()
        this.date = this.formatDate(today)
    },
    formatDate(date) {
        const d = String(date.getDate()).padStart(2,'0')
        const m = String(date.getMonth()+1).padStart(2,'0')
        const y = date.getFullYear()
        return `${d}.${m}.${y}`
    },
    fromCalendar(value) {
        const [y,m,d] = value.split('-')
        this.date = `${d}.${m}.${y}`
    },
    download() {
        window.location.href = `/reports/get_report_excel?date=${this.date}`
    }
}
}