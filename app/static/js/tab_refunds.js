function refundsTable() {
  return {
    rows: [],
    loading: false,
    error: '',
    currentPage: 1,
    pageSize: 25,

    search: '',
    statusFilter: 'all',
    typeFilter: 'any',
    selectedDate: '',

    async init() {
      this.selectedDate = "02.04.2026";
      await this.loadData();
    },

    async loadData() {
      this.loading = true;
      this.error = '';

      try {
        const response = await fetch('/reports/data?date=02.04.2026');

        console.log('FETCH STATUS:', response.status);

        const data = await response.json();
        console.log('DATA:', data);

        this.rows = Array.isArray(data.rows) ? data.rows : [];
        console.log('ROWS LOADED:', this.rows.length);
        console.log('FIRST ROW:', this.rows[0]);

        this.currentPage = 1;
      } catch (error) {
        console.error('Ошибка загрузки данных:', error);
        this.rows = [];
        this.error = 'Не удалось загрузить данные';
      } finally {
        this.loading = false;
      }
    },

    get filteredRows() {
      return this.rows.filter(row => {
        const rowStatus = String(row.status ?? '');
        const rowType = String(row.type_payer ?? '').trim().toUpperCase();
        const knp = String(row.knp ?? '');

        const searchValue = this.search.trim().toLowerCase();
        const refer = String(row.refer_in ?? '').toLowerCase();
        const iin = String(row.iin ?? '').toLowerCase();

        const matchesSearch =
          !searchValue ||
          refer.includes(searchValue) ||
          iin.includes(searchValue);

        const matchesStatus =
          this.statusFilter === 'all' ||
          rowStatus === this.statusFilter;

        const matchesType =
          this.typeFilter === 'any' ||
          (this.typeFilter === 'СО' && knp === '026') ||
          (this.typeFilter === 'ЕП' && knp === '094');

        return matchesSearch && matchesStatus && matchesType;
      });
    },

    get totalPages() {
      return Math.max(1, Math.ceil(this.filteredRows.length / this.pageSize));
    },

    get paginatedRows() {
      const start = (this.currentPage - 1) * this.pageSize;
      const end = start + this.pageSize;
      return this.filteredRows.slice(start, end);
    },

    get totalPaySum() {
      return this.filteredRows.reduce((sum, row) => sum + this.toNumber(row.pay_sum), 0);
    },

    get totalRefundSum() {
      return this.filteredRows.reduce((sum, row) => sum + this.toNumber(row.sum_gfss), 0);
    },

    get startRow() {
      if (this.filteredRows.length === 0) return 0;
      return (this.currentPage - 1) * this.pageSize + 1;
    },

    get endRow() {
      return Math.min(this.currentPage * this.pageSize, this.filteredRows.length);
    },

    get visiblePages() {
      const total = this.totalPages;
      const current = this.currentPage;
      const maxVisible = 5;

      let start = Math.max(1, current - 2);
      let end = Math.min(total, start + maxVisible - 1);

      if (end - start < maxVisible - 1) {
        start = Math.max(1, end - maxVisible + 1);
      }

      const pages = [];
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      return pages;
    },

    goToPage(page) {
      if (page < 1) page = 1;
      if (page > this.totalPages) page = this.totalPages;
      this.currentPage = page;
    },

    prevPage() {
      if (this.currentPage > 1) this.currentPage--;
    },

    nextPage() {
      if (this.currentPage < this.totalPages) this.currentPage++;
    },

    toNumber(value) {
      if (value === null || value === undefined || value === '') return 0;
      if (typeof value === 'number') return value;

      const normalized = String(value)
        .replace(/\s/g, '')
        .replace(',', '.');

      const parsed = parseFloat(normalized);
      return Number.isNaN(parsed) ? 0 : parsed;
    },

    formatAmount(value) {
      return new Intl.NumberFormat('ru-RU', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(value || 0);
    },

    formatToday() {
      const now = new Date();
      const day = String(now.getDate()).padStart(2, '0');
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const year = now.getFullYear();
      return `${day}.${month}.${year}`;
    }
  };
}