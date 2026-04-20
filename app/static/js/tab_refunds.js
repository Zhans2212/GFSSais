function refundsTable() {
  return {
    rows: [],
    loading: false,
    error: '',
    currentPage: 1,
    pageSize: 15,

    search: '',
    statusFilter: '1',
    typeFilter: 'any',

    openFilter: null, // какой столбец сейчас открыт
    columnFilters: {
      sior_id: { op: 'contains', value: '' },
      refer_in: { op: 'contains', value: '' },
      bin: { op: 'contains', value: '' },
      doc_nmb: { op: 'contains', value: '' },
      doc_date: { op: 'contains', value: '' },
      pay_sum: { op: 'contains', value: '' },
      ret_sum: { op: 'contains', value: '' },
      status: { op: 'contains', value: '' },
      knp: { op: 'contains', value: '' },
      code1c: { op: 'contains', value: '' },
      type_payer: { op: 'contains', value: '' },
      ret_date: { op: 'contains', value: '' },
      recv_date: { op: 'contains', value: '' },
      c1_doc_date: { op: 'contains', value: '' },
    },

    columns: [
      { key: 'sior_id', label: '№' },
      { key: 'refer_in', label: 'Референс' },
      { key: 'bin', label: 'БИН отправ.' },
      { key: 'doc_nmb', label: '№ плат.поруч.' },
      { key: 'doc_date', label: 'Дата плат.' },
      { key: 'pay_sum', label: 'Сумма платежа' },
      { key: 'ret_sum', label: 'Сумма возврата' },
      { key: 'status', label: 'Статус' },
      { key: 'knp', label: 'КНП' },
      { key: 'code1c', label: 'Тип возврата' },
      { key: 'type_payer', label: 'Тип плательщика' },
      { key: 'ret_date', label: 'Дата ООП' },
      { key: 'recv_date', label: 'Дата ГФСС' },
      { key: 'c1_doc_date', label: 'Дата 1С' },
    ],

    accessToApprove: false,
    acceptRadio: 'all',

    personLoading: false,
    personError: '',
    personsRows: [],
    siorID: '',

    reportLoading: false,
    reportError: '',
    reportRows: [],
    reportDate: '',
    total: {},

    async init() {
      await this.loadData();
      await this.checkAccess();
    },

    async checkAccess() {
      try {
        const response = await fetch(`/reports/access-to-approve`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        this.accessToApprove = data === true;
      } catch (e) {
        console.error('Ошибка проверки доступа:', e);
        this.accessToApprove = false;
      }
    },

    get canApprove() {
      return this.accessToApprove && this.statusFilter === '1';
    },

    async loadData() {
      this.loading = true;
      this.error = '';

      try {
        const response = await fetch(`/reports/data?status=${encodeURIComponent(this.statusFilter)}`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        console.log('DATA:', data);

        this.rows = Array.isArray(data.rows) ? data.rows : [];
        this.currentPage = 1;
      } catch (error) {
        console.error('Ошибка загрузки данных:', error);
        this.rows = [];
        this.error = 'Не удалось загрузить данные';
      } finally {
        this.loading = false;
      }
    },

    // НАЙТИ ЛЮДЕЙ ПО НОМЕРУ ЗАЯВКИ
    async loadPersons(sior_id) {
      this.personLoading = true;
      this.personError = '';
      this.siorID = sior_id;

      try {
        const response = await fetch(`/reports/persons?sior_id=${encodeURIComponent(this.siorID)}`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        console.log('PERSONS_DATA:', data);

        this.personsRows = Array.isArray(data.rows) ? data.rows : [];
      } catch (error) {
        console.error('Ошибка загрузки людей:', error);
        this.personsRows = [];
        this.personError = 'Не удалось загрузить данные по людям';
      } finally {
        this.personLoading = false;
      }
    },

    // ФОРМИРОВАНИЕ ОТЧЕТА ПОД ТАБЛИЦЕЙ
    async loadReport(date) {
      this.reportLoading = true;
      this.reportError = '';
      this.reportDate = date;

      try {
        const response = await fetch(`/reports/order-data?date=${encodeURIComponent(this.reportDate)}`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        console.log('REPORT DATA:', data);

        this.reportRows = Array.isArray(data.rows) ? data.rows : [];
        this.total = data.total || {};
      } catch (error) {
        console.error('Ошибка загрузки отчета:', error);
        this.reportRows = [];
        this.total = {};
        this.reportError = 'Не удалось загрузить данные отчета';
      } finally {
        this.reportLoading = false;
      }
    },

    async acceptAll() {
      this.loading = true;

      try {
        const response = await fetch(`/reports/accept_all?typ=${encodeURIComponent(this.acceptRadio)}`,
            {method: 'POST'});

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        await this.loadData();
      } catch (error) {
        console.error('Ошибка утверждения с 1 по 2 статус:', error);
      } finally {
        this.loading = false;
      }
    },

    // Получить дату из таблицы возвратов для формирования отчета
    getReportDateFromRefunds() {
      const sourceRow = this.filteredRows?.[0] || this.rows?.[0];
      if (!sourceRow || !sourceRow.recv_date) return '';

      if (this.statusFilter === '2') return this.formatRefundDate(sourceRow.recv_date);
      return '';
    },

    formatRefundDate(value) {
      if (!value) return '';

      // ожидаемый формат: 09-04-2026 04:36:17
      const datePart = String(value).split(' ')[0]; // 09-04-2026
      const [day, month, year] = datePart.split('-');

      if (!day || !month || !year) return '';

      return `${day}.${month}.${year}`; // 09.04.2026
    },

    // Фильтры
    toggleFilter(col) {
      this.openFilter = this.openFilter === col ? null : col;
    },

    closeFilters() {
      this.openFilter = null;
    },

    applyFilter(cellValue, filter) {
      if (!filter || !filter.value) return true;

      const val = String(cellValue ?? '').toLowerCase();
      const search = String(filter.value).toLowerCase();

      switch (filter.op) {
        case 'eq': return val === search;
        case 'neq': return val !== search;
        case 'starts': return val.startsWith(search);
        case 'ends': return val.endsWith(search);
        case 'contains': return val.includes(search);
        case 'not_contains': return !val.includes(search);
        default: return true;
      }
    },

    get filteredRows() {
      return this.rows.filter(row => {

        const matchesColumns = Object.entries(this.columnFilters).every(([key, filter]) => {
          return this.applyFilter(row[key], filter);
        });

        const rowStatus = String(row.status ?? '');

        const matchesStatus =
          this.statusFilter === 'all' ||
          rowStatus === this.statusFilter;

        const type_payer = String(row.type_payer ?? '').toUpperCase();
        const code1c = String(row.code1c ?? '').toUpperCase();

        const matchesType =
          this.typeFilter === 'any' ||
          (this.typeFilter === 'СЗ' && type_payer === 'СЗ') ||
          (this.typeFilter === 'СО' && code1c === 'СО') ||
          (this.typeFilter === 'ЕП' && code1c === 'ЕП');

        return matchesColumns && matchesStatus && matchesType;
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
      return this.filteredRows.reduce((sum, row) => sum + this.toNumber(row.ret_sum), 0);
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

    downloadExcel() {
      const date = this.reportDate || this.getReportDateFromRefunds();
      window.location.href = `/reports/get_report_excel?date=${encodeURIComponent(date)}`;
    },

    downloadPdf() {
      const date = this.reportDate || this.getReportDateFromRefunds();
      window.location.href = `/reports/get_report_pdf?date=${encodeURIComponent(date)}`;
    },
  };
}


    // Открытие модального окна с инфо о человеке
    // async openPersonModal(iin) {
    //   this.person = null;
    //   this.personError = '';
    //   this.personLoading = true;
    //
    //   const modal = document.getElementById('my_modal_2');
    //   if (modal) {
    //     modal.showModal();
    //   }
    //
    //   try {
    //     const response = await fetch(`/reports/person/${encodeURIComponent(iin)}`);
    //
    //     if (!response.ok) {
    //       throw new Error(`HTTP ${response.status}`);
    //     }
    //
    //     this.person = await response.json();
    //   } catch (error) {
    //     console.error('Ошибка загрузки данных физлица:', error);
    //     this.person = null;
    //     this.personError = 'Не удалось загрузить данные';
    //   } finally {
    //     this.personLoading = false;
    //   }
    // }