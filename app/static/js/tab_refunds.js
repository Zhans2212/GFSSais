function refundsTable() {
  return {
    initialized: false,

    rows: [],
    loading: false,
    error: '',
    currentPage: 1,
    pageSize: 15,

    search: '',
    statusFilter: '1',
    typeFilter: 'any',

    openFilter: null, // фильтр столбцов
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
    selectedSiorID: '',
    filteredSiors: [],

    reportLoading: false,
    reportError: '',
    reportRows: [],
    row026: null,
    row094: null,

    filters: {
      sior_id: '',
      refer_in: '',
    },

    async init() {
      if (this.initialized) return;
      this.initialized = true;

      await this.checkAccess()
      await this.loadData()
      await this.loadPersons()
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

    async loadData(filters = null) {
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
    async loadPersons() {
      this.personLoading = true;
      this.personError = '';

      try {
        const response = await fetch(`/reports/persons?status=${encodeURIComponent(this.statusFilter)}`);

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

    selectPerson() {
      let result = this.personsRows;

      if (this.selectedSiorID) {
        result = result.filter(p => p.sior_id === this.selectedSiorID);
      }

      return result;
    },

    get filteredSiorIds() {
      return new Set(this.filteredRows.map(row => row.sior_id));
    },

    get filteredPersonsByMainTable() {
      const siorIds = this.filteredSiorIds;

      return this.personsRows.filter(person =>
        siorIds.has(person.sior_id)
      );
    },

    // ФОРМИРОВАНИЕ ОТЧЕТА ПОД ТАБЛИЦЕЙ
    async loadReport() {
      this.reportLoading = true;
      this.reportError = '';

      try {
        const response = await fetch(`/reports/418-data`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        console.log('REPORT DATA:', data);

        this.reportRows = Array.isArray(data.rows) ? data.rows : [];
        this.row026 = this.reportRows.find(r => r.knp === '026')
        this.row094 = this.reportRows.find(r => r.knp === '094')
      } catch (error) {
        console.error('Ошибка загрузки отчета:', error);
        this.reportRows = [];
        this.reportError = 'Не удалось загрузить данные отчета';
      } finally {
        this.reportLoading = false;
      }
    },

    getRowTotal(row) {
      return {
        cnt: (row?.cnt_so || 0) + (row?.cnt_ep || 0) + (row?.cnt_sz || 0),
        sum: (row?.sum_so || 0) + (row?.sum_ep || 0) + (row?.sum_sz || 0),
      };
    },

    // ОДОБРИТЬ ЗАЯВКИ
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

    // Фильтры
    isFilterActive(col) {
      const f = this.columnFilters[col];
      return f && f.value && f.value.toString().trim() !== '';
    },

    clearFilter(col) {
      if (this.columnFilters[col]) {
        this.columnFilters[col].value = '';
      }
    },

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
          (this.typeFilter === 'СО' && code1c === 'СО' && type_payer !== 'СЗ') ||
          (this.typeFilter === 'ЕП' && code1c === 'ЕП' && type_payer !== 'СЗ');

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
      window.location.href = `/reports/get_report_excel`;
    },

    downloadPdf() {
      window.location.href = `/reports/get_report_pdf`;
    },

    get canSeeFilters() {
      return this.statusFilter !== '1' && this.statusFilter !== '2';
    },

    async loadFilteredData(filters = null) {
      this.loading = true;
      this.error = '';

      try {
        const response = await fetch(`/reports/data1c?status=${encodeURIComponent(this.statusFilter)}`, {method: 'POST',
                                                                           headers: {'Content-Type': 'application/json'},
                                                                           body: JSON.stringify(filters)
                                                                           });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        if (response.status === 422) {
          const err = await response.json();
          this.error = 'Обязательные поля не заполнены';
          return;
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

    async applyFilters() {
      const cleaned = Object.fromEntries(
        Object.entries(this.filters).filter(
          ([_, v]) => v !== '' && v !== null
        )
      );

      console.log('Фильтры:', cleaned);

      await this.loadFilteredData(cleaned);
    },

    async resetFilters() {
      this.filters = {
        sicid: '',
        pay_date: '',
        p_rnn: '',
        knp: '',
        sum_from: '',
        sum_to: '',
        period: ''
      };

      this.rows = []
    },
  };
}