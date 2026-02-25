function reportsTabs(payload = {}) {
return {
  top_control: payload.top_control,
  maxTabs: 6,
  tabs: [],
  activeId: null,
  counters: { returns: 0, wrong: 0 },
  confirmCloseAllOpen: false,

  async loadPerson(tab, iin) {
    tab.state.selectedIin = iin;
    tab.state.personPanelOpen = true;
    tab.state.loadingPerson = true;
    tab.state.personError = null;
    tab.state.person = null;

    try {
      const resp = await fetch(`/reports/person/${encodeURIComponent(iin)}`);
      if (!resp.ok) throw new Error('HTTP error');

      const data = await resp.json();
      if (!data) {
        tab.state.personError = 'Данные не найдены';
      } else {
        tab.state.person = data;
      }
    } catch (e) {
      tab.state.personError = 'Ошибка загрузки данных';
    } finally {
      tab.state.loadingPerson = false;
    }
  },

  storageKey: 'reportsTabsState:v1',
  _saveTimer: null,

  init() {
    console.log('Инициализация:', this.top_control, this.username);

    this.restore();

    // автосохранение при изменениях
    this.$watch('tabs', () => this.scheduleSave(), { deep: true });
    this.$watch('activeId', () => this.scheduleSave());
    this.$watch('counters', () => this.scheduleSave(), { deep: true });
  },
  snapshotForSave() {
    return {
      activeId: this.activeId,
      counters: this.counters,
      tabs: this.tabs.map(t => ({
        id: t.id,
        kind: t.kind,
        title: t.title,
        state: {
          status: t.state.status,
          type: t.state.type,
          query: t.state.query,

          selectedIin: t.state.selectedIin,
          personPanelOpen: t.state.personPanelOpen
        }
      }))
    };
  },

  scheduleSave() {
    clearTimeout(this._saveTimer);
    this._saveTimer = setTimeout(() => this.save(), 300);
  },

  save() {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.snapshotForSave()));
    } catch (e) {
      // если storage переполнен или запрещён — просто молчим
    }
  },

  restore() {
    try {
      const raw = localStorage.getItem(this.storageKey);
      if (!raw) return;

      const data = JSON.parse(raw);
      if (!data || !Array.isArray(data.tabs)) return;

      this.counters = data.counters || { returns: 0, wrong: 0 };

      this.tabs = data.tabs.slice(0, this.maxTabs).map(t => ({
        id: t.id || `${t.kind}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
        kind: t.kind,
        title: t.title || (t.kind === 'returns' ? 'Возвраты СО' : 'Ошибочные заявки'),
        state: {
          status: t.state?.status ?? 'all',
          type: t.state?.type ?? 'any',
          query: t.state?.query ?? '',

          selectedIin: t.state?.selectedIin ?? null,
          personPanelOpen: t.state?.personPanelOpen ?? false,

          // эти поля не сохраняем — они живые
          loadingPerson: false,
          personError: null,
          person: null,

          totals: { totalSum: 0, totalRefund: 0, count: 0 }
        }
      }));

      this.activeId =
        data.activeId && this.tabs.some(x => x.id === data.activeId)
          ? data.activeId
          : (this.tabs[0]?.id ?? null);

      // если надо — подтянуть данные выбранных людей после восстановления
      this.tabs.forEach(t => {
        if (t.state.selectedIin) this.loadPerson(t, t.state.selectedIin);
      });
    } catch (e) {
      // битый JSON — игнорируем
    }
  },

  clearSavedState() {
    localStorage.removeItem(this.storageKey);
  },

  recalcTotals(tab, rootEl) {
    if (!tab || !rootEl) return;

    const rows = rootEl.querySelectorAll("tbody tr");

    let totalSum = 0;
    let totalRefund = 0;
    let count = 0;

    rows.forEach((row) => {
      const style = getComputedStyle(row).display;
      if (style === "none") return;

      const sumText = (row.cells[5]?.innerText ?? "").replace(/,/g, "");
      const refundText = (row.cells[6]?.innerText ?? "").replace(/,/g, "");

      totalSum += parseFloat(sumText) || 0;
      totalRefund += parseFloat(refundText) || 0;
      count += 1;
    });

    tab.state.totals = {
      totalSum,
      totalRefund,
      count
    };
  },

  openTab(kind) {
    if (this.tabs.length >= this.maxTabs) return;

    this.counters[kind] += 1;

    const titleBase = kind === 'returns' ? 'Возвраты СО' : 'Ошибочные заявки';
    const title = this.counters[kind] > 1 ? `${titleBase} #${this.counters[kind]}` : titleBase;

    const id = `${kind}-${Date.now()}-${Math.random().toString(16).slice(2)}`;

    const newTab = {
      id,
      kind,
      title,
      state: {
        status: 'all',
        type: 'any',
        query: '',

        // состояние выбранного человека — ВНУТРИ вкладки
        selectedIin: null,
        personPanelOpen: false,
        loadingPerson: false,
        personError: null,
        person: null
      }
    };

    this.tabs.push(newTab);
    this.activeId = id;
  },

  closeTab(id) {
    const idx = this.tabs.findIndex(t => t.id === id);
    if (idx === -1) return;

    const wasActive = this.activeId === id;
    this.tabs.splice(idx, 1);

    if (!wasActive) return;

    this.counters[this.tabs[idx - 1]?.kind ?? 'returns'] -= 1;

    const next = this.tabs[idx] || this.tabs[idx - 1] || null;
    this.activeId = next ? next.id : null;
  },

  requestCloseAll() {
    if (this.tabs.length === 0) return;
    this.confirmCloseAllOpen = true;
  },
  confirmCloseAll() {
    this.closeAll();
    this.confirmCloseAllOpen = false;
  },

  closeAll() {
    this.tabs.splice(0, this.tabs.length);
    this.counters = { returns: 0, wrong: 0 };
    this.clearSavedState();
  },

  rowVisible(tab, status, typePayer, referIn, iin) {
    if (tab.state.status !== 'all' && String(status) !== String(tab.state.status)) return false;
    if (tab.state.type !== 'any' && String(typePayer) !== String(tab.state.type)) return false;

    const q = (tab.state.query || '').toLowerCase();
    if (!q) return true;

    const hay = `${referIn ?? ''} ${iin ?? ''}`.toLowerCase();
    return hay.includes(q);
  },

  async requestAcceptAll() {
    try {
      const activeSection = Array.from(document.querySelectorAll("section")).find(
        (s) => getComputedStyle(s).display !== "none"
      ) || document;

      const rows = activeSection.querySelectorAll("tbody tr");

      const siorIds = new Set();
      rows.forEach((row) => {
        if (getComputedStyle(row).display === "none") return;

        const v = row.dataset.siorId;
        if (v) siorIds.add(Number(v));
      });

      const payload = { sior_ids: Array.from(siorIds) };

      if (payload.sior_ids.length === 0) {
        alert("Нет записей для согласования");
        return;
      }

      const resp = await fetch("/reports/accept_all", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify(payload)
      });

      if (!resp.ok) {
        alert("Ошибка согласования");
        return;
      }

      window.location.reload();
    } catch (e) {
      alert("Ошибка согласования");
    }
  }

};
}
