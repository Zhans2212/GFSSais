function refundsTable() {
  return {
    rows: [],
    loading: false,
    error: '',
    currentPage: 1,
    pageSize: 15,

    search: '',
    statusFilter: 'all',
    typeFilter: 'any',
    selectedDate: '02.04.2026',

    person: null,
    personLoading: false,
    personError: '',

    async init() {
      await this.loadData();
    },

    async loadData() {
      this.loading = true;
      this.error = '';

      try {
        const response = await fetch(`/reports/data?date=${encodeURIComponent(this.selectedDate)}`);
        console.log('FETCH STATUS:', response.status);

        const text = await response.text();
        const data = JSON.parse(text);

        console.log('DATA:', data);

        this.rows = Array.isArray(data.rows) ? data.rows : [];
        console.log('ROWS LOADED:', this.rows.length);

        this.currentPage = 1;
      } catch (error) {
        console.error('Ошибка загрузки данных:', error);
        this.rows = [];
        this.error = 'Не удалось загрузить данные';
      } finally {
        this.loading = false;
      }
    },

    // Фильтры по статусу и типу возврата
    get filteredRows() {
      return this.rows.filter(row => {
        const rowStatus = String(row.status ?? '');
        const knp = String(row.knp ?? '').padStart(3, '0');

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

    // Подсчет данных
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

    // Пагинация
    goToFirstPage() {
      this.currentPage = 1;
    },

    goToLastPage() {
      this.currentPage = this.totalPages;
    },

    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--;
      }
    },

    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++;
      }
    },

    // Форматирование в число
    toNumber(value) {
      if (value === null || value === undefined || value === '') return 0;
      if (typeof value === 'number') return value;

      const normalized = String(value)
        .replace(/\s/g, '')
        .replace(',', '.');

      const parsed = parseFloat(normalized);
      return Number.isNaN(parsed) ? 0 : parsed;
    },

    // Формат чисел
    formatAmount(value) {
      return new Intl.NumberFormat('ru-RU', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(value || 0);
    },

    // Открытие модального окна с инфо о человеке
    async openPersonModal(iin) {
      this.person = null;
      this.personError = '';
      this.personLoading = true;

      const modal = document.getElementById('my_modal_2');
      if (modal) {
        modal.showModal();
      }

      try {
        const response = await fetch(`/reports/person/${encodeURIComponent(iin)}`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        this.person = await response.json();
      } catch (error) {
        console.error('Ошибка загрузки данных физлица:', error);
        this.person = null;
        this.personError = 'Не удалось загрузить данные';
      } finally {
        this.personLoading = false;
      }
    }
  };
}

// ФОРМИРОВАНИЕ ОТЧЕТА ПОД ТАБЛИЦЕЙ
function orderReport() {
  return {
    rows: [],
    total: {},
    loading: false,
    error: '',
    reportDate: '',
    selectedDate: '',

    init() {
      this.selectedDate = '02.04.2026';
      this.loadReport();
    },

    getToday() {
      const now = new Date();
      const day = String(now.getDate()).padStart(2, '0');
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const year = now.getFullYear();
      return `${day}.${month}.${year}`;
    },

    async loadReport() {
      this.loading = true;
      this.error = '';

      try {
        const response = await fetch(`/reports/order-data?date=${encodeURIComponent(this.selectedDate)}`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        this.rows = Array.isArray(data.rows) ? data.rows : [];
        this.total = data.total || {};
        this.reportDate = data.date || this.selectedDate;
      } catch (error) {
        console.error('Ошибка загрузки отчета:', error);
        this.rows = [];
        this.total = {};
        this.error = 'Не удалось загрузить данные отчета';
      } finally {
        this.loading = false;
      }
    },

    downloadExcel() {
      window.location.href = `/reports/get_report_excel?date=${encodeURIComponent(this.selectedDate)}`;
    },

    downloadPdf() {
      window.location.href = `/reports/get_report_pdf?date=${encodeURIComponent(this.selectedDate)}`;
    },

    formatAmount(value) {
      const num = Number(value || 0);
      return new Intl.NumberFormat('ru-RU', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(num);
    }
  };
}