let appData = {
  summary: {},
  results: [],
  catalog: [],
  policies: [],
  sales_reps: [],
};
let selectedRequestId = null;
let currentFilter = 'all';
let searchQuery = '';
let topHeroMode = 'chart'; // 'chart' | 'workflow'
let miniDetailTab = 'fin'; // 'fin' | 'guard' | 'ops'
let activeSimStep = null;
let llmConfig = {
  provider: 'gemini',
  api_key: '',
};

const AVATAR_COLORS = [
  'from-pink-500 to-rose-500',
  'from-blue-600 to-indigo-600',
  'from-amber-500 to-orange-600',
  'from-emerald-500 to-teal-600',
  'from-purple-600 to-indigo-600',
  'from-cyan-500 to-blue-600',
];

function formatVND(num) {
  if (num === null || num === undefined || isNaN(num)) return '0 VNĐ';
  return Math.round(Number(num)).toLocaleString('vi-VN') + ' VNĐ';
}

function formatShortVND(num) {
  if (!num || isNaN(num)) return '0 đ';
  const n = Number(num);
  if (n >= 1_000_000_000) return (n / 1_000_000_000).toFixed(2).replace('.', ',') + ' tỷ';
  if (n >= 1_000_000) return Math.round(n / 1_000_000).toLocaleString('vi-VN') + ' tr';
  return n.toLocaleString('vi-VN') + ' đ';
}

function getInitials(name) {
  if (!name) return 'KH';
  const parts = name
    .replace(/Công ty|Cổ phần|TNHH|Tập đoàn|Ngân hàng|Bệnh viện/gi, '')
    .trim()
    .split(/\s+/);
  if (parts.length >= 2) {
    return (parts[parts.length - 2][0] + parts[parts.length - 1][0]).toUpperCase();
  }
  return name.slice(0, 2).toUpperCase();
}

// Smooth Number Counter Animation
function animateValue(elId, endValue, formatter = null, duration = 550) {
  const el = document.getElementById(elId);
  if (!el) return;
  const startValue = Number(el.dataset.rawVal || 0);
  el.dataset.rawVal = endValue;
  const startTime = performance.now();

  function step(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(startValue + (endValue - startValue) * eased);
    el.textContent = formatter ? formatter(current) : current.toLocaleString('vi-VN');
    if (progress < 1) {
      requestAnimationFrame(step);
    } else {
      el.textContent = formatter ? formatter(endValue) : endValue.toLocaleString('vi-VN');
    }
  }
  requestAnimationFrame(step);
}

let toastTimer = null;
function showStatusAlert(msg, type = 'info') {
  const el = document.getElementById('floatingToast');
  if (!el) return;
  const styles = {
    info: 'bg-[#0d1226] text-white border border-slate-700 shadow-2xl',
    success: 'bg-[#0d1226] text-white border-l-4 border-l-emerald-400 shadow-2xl',
    error: 'bg-rose-600 text-white shadow-2xl',
  };
  const icons = {
    info: 'fa-spinner fa-spin text-[#f5b027]',
    success: 'fa-circle-check text-emerald-400',
    error: 'fa-triangle-exclamation text-white',
  };
  el.className = `fixed top-5 right-5 z-50 max-w-md px-4 py-3 rounded-2xl text-xs font-bold flex items-center justify-between gap-3 panel-pop ${
    styles[type] || styles.info
  }`;
  el.innerHTML = `
    <div class="flex items-center gap-2.5">
      <i class="fa-solid ${icons[type] || icons.info} text-sm"></i>
      <span class="leading-snug">${msg}</span>
    </div>
    <button onclick="document.getElementById('floatingToast').classList.add('hidden')" class="text-white/60 hover:text-white">
      <i class="fa-solid fa-xmark"></i>
    </button>
  `;
  el.classList.remove('hidden');
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    el.classList.add('hidden');
  }, 4500);
}

function toggleModal(id) {
  const m = document.getElementById(id);
  if (!m) return;
  if (m.classList.contains('hidden')) {
    m.classList.remove('hidden');
    m.classList.add('flex');
  } else {
    m.classList.add('hidden');
    m.classList.remove('flex');
  }
}

function switchMainSection(secName) {
  ['overview', 'workflow', 'catalog', 'reps'].forEach((s) => {
    const el = document.getElementById(`section-${s}`);
    const rail = document.getElementById(`rail-${s}`);
    if (el) {
      if (s === secName) el.classList.remove('hidden');
      else el.classList.add('hidden');
    }
    if (rail) {
      if (s === secName) rail.classList.add('active');
      else rail.classList.remove('active');
    }
  });
}

function openAndScrollDeepDive() {
  switchMainSection('overview');
  scrollToElement('activeOpportunityDeepDive');
}

function filterOrdersAndFocus(filterType) {
  switchMainSection('overview');
  setQueueFilter(filterType);
  scrollToElement('recentOrdersContainer');
}

function handleGlobalSearch(val) {
  searchQuery = (val || '').trim().toLowerCase();
  const clearBtn = document.getElementById('clearSearchBtn');
  if (clearBtn) {
    if (searchQuery) clearBtn.classList.remove('hidden');
    else clearBtn.classList.add('hidden');
  }
  renderRecentOrdersCard();
}

function clearGlobalSearch() {
  const inp = document.getElementById('globalSearchInput');
  if (inp) inp.value = '';
  handleGlobalSearch('');
}

function switchTopHeroMode(mode) {
  topHeroMode = mode;
  const btnChart = document.getElementById('heroBtn-chart');
  const btnWf = document.getElementById('heroBtn-workflow');
  const chartBox = document.getElementById('topHeroChartContainer');
  const wfBox = document.getElementById('topHeroWorkflowContainer');

  if (mode === 'chart') {
    btnChart.className = 'px-4 py-2 rounded-xl bg-[#0d1226] text-white text-xs font-bold shadow-sm transition flex items-center gap-1.5';
    btnWf.className = 'px-4 py-2 rounded-xl bg-[#f4f5f9] text-slate-600 hover:text-[#0d1226] text-xs font-bold transition flex items-center gap-1.5';
    chartBox.classList.remove('hidden');
    wfBox.classList.add('hidden');
  } else {
    btnWf.className = 'px-4 py-2 rounded-xl bg-[#0d1226] text-white text-xs font-bold shadow-sm transition flex items-center gap-1.5';
    btnChart.className = 'px-4 py-2 rounded-xl bg-[#f4f5f9] text-slate-600 hover:text-[#0d1226] text-xs font-bold transition flex items-center gap-1.5';
    wfBox.classList.remove('hidden');
    chartBox.classList.add('hidden');
  }
}

function switchMiniDetailTab(tab) {
  miniDetailTab = tab;
  ['fin', 'guard', 'ops'].forEach((t) => {
    const btn = document.getElementById(`miniTab-${t}`);
    if (!btn) return;
    if (t === tab) {
      btn.className = 'px-2.5 py-1 rounded-lg bg-[#0d1226] text-white shadow-sm transition';
    } else {
      btn.className = 'px-2.5 py-1 rounded-lg text-slate-500 hover:text-slate-900 transition';
    }
  });
  renderMiniDetailCard();
}

// Live Step-by-Step AI Workflow Simulation Effect
async function runLiveStepSimulation() {
  switchMainSection('overview');
  switchTopHeroMode('workflow');
  const item = getSelectedItem();
  if (!item) return;

  showStatusAlert(`Đang mô phỏng AI Agent duyệt từng bước cho hồ sơ ${item.ma_yeu_cau}...`, 'info');
  const steps = item.is_info_complete ? [1, 2, 3, 5, 6, 7, 8] : [1, 2, 3, 4, 8];
  for (const s of steps) {
    activeSimStep = s;
    renderTopHeroCard();
    await new Promise((r) => setTimeout(r, 420));
  }
  activeSimStep = null;
  renderTopHeroCard();
  showStatusAlert(`Hoàn tất mô phỏng quy trình cho ${item.ten_khach_hang} (${item.final_status})!`, 'success');
}

async function fetchInitialData() {
  try {
    showStatusAlert('Đang khởi tạo AI Agent & phân tích dữ liệu Công ty Minh An...', 'info');
    const res = await fetch('/api/analyze-all', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        llm_provider: llmConfig.provider,
        llm_api_key: llmConfig.api_key,
      }),
    });
    const data = await res.json();
    updateUIWithData(data);
    showStatusAlert(
      `Sẵn sàng! Đã phân tích ${data.results.length} yêu cầu B2B • Đối chiếu ${data.catalog.length} SP & ${data.policies.length} chính sách duyệt.`,
      'success'
    );
  } catch (err) {
    showStatusAlert('Lỗi khi tải dữ liệu: ' + err.message, 'error');
  }
}

function updateUIWithData(data, preferId = null) {
  appData = data;

  if (preferId) {
    selectedRequestId = preferId;
  } else if (!selectedRequestId || !appData.results.find((r) => r.ma_yeu_cau === selectedRequestId)) {
    selectedRequestId = appData.results.length > 0 ? appData.results[0].ma_yeu_cau : null;
  }

  renderQuickCustomerChips();
  renderRightColumnCards();
  renderTopHeroCard();
  renderMiniDetailCard();
  renderRecentOrdersCard();
  renderDeepDiveWorkspace();
  renderCatalogAndPolicies();
}

function getSelectedItem() {
  return (appData.results || []).find((r) => r.ma_yeu_cau === selectedRequestId) || appData.results[0];
}

function renderQuickCustomerChips() {
  const box = document.getElementById('quickCustomerChips');
  if (!box || !appData.results) return;
  box.innerHTML = appData.results
    .map((r) => {
      const isSel = r.ma_yeu_cau === selectedRequestId;
      const dotColor = !r.is_info_complete
        ? 'bg-[#f06449]'
        : r.approval.requires_manager_approval
        ? 'bg-purple-500'
        : 'bg-emerald-500';
      return `
        <button
          onclick="selectRequest('${r.ma_yeu_cau}')"
          class="px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
            isSel
              ? 'bg-[#0d1226] text-white shadow-md scale-105'
              : 'bg-[#f4f5f9] text-slate-600 hover:bg-slate-200'
          }"
        >
          <span class="w-2 h-2 rounded-full ${dotColor}"></span>
          <span>${r.ma_yeu_cau.replace('YC-2026-', 'YC-')}</span>
        </button>
      `;
    })
    .join('');
}

// ============================================================================
// 1. RENDER RIGHT COLUMN (AMBER BALANCE + CORAL APPROVAL + 2x3 SALES GRID)
// ============================================================================
function renderRightColumnCards() {
  const s = appData.summary || {};
  const item = getSelectedItem();

  const railMgr = document.getElementById('railBadgeManager');
  const railTot = document.getElementById('railBadgeTotal');
  if (railMgr) railMgr.textContent = s.need_manager_count || 0;
  if (railTot) railTot.textContent = s.total_requests || 0;

  const sel = document.getElementById('quickRequestSelector');
  if (sel && appData.results) {
    sel.innerHTML = appData.results
      .map(
        (r) =>
          `<option value="${r.ma_yeu_cau}" ${r.ma_yeu_cau === selectedRequestId ? 'selected' : ''}>
            ${r.ma_yeu_cau} — ${r.ten_khach_hang}
          </option>`
      )
      .join('');
  }

  if (!item) return;

  // Card 1: Warm Amber Balance Card
  document.getElementById('amberCardLabel').textContent = `TỔNG PIPELINE B2B (${s.complete_count}/${s.total_requests} HỒ SƠ ĐỦ TT)`;
  animateValue('amberCardValue', s.total_pipeline_value || 0, formatVND);
  document.getElementById('amberCardSub').textContent = item.is_info_complete
    ? `Đang chọn ${item.ma_yeu_cau}: ${formatVND(item.financials.tong_sau_chiet_khau)} (CK ${item.financials.ap_dung_chiet_khau_pct}%)`
    : `Đang chọn ${item.ma_yeu_cau}: Cần KH làm rõ SL / Ngân sách`;

  // Card 2: Soft Gray Approval Card
  const ap = item.approval;
  document.getElementById('coralCardPolicyBadge').textContent = ap.policy_code;
  document.getElementById('coralCardLabel').textContent = `PHÂN QUYỀN DUYỆT • ${item.ma_ho_so_co_hoi}`;
  document.getElementById('coralCardValue').textContent = !item.is_info_complete
    ? 'Chờ KH Làm rõ TT'
    : ap.requires_manager_approval
    ? ap.approval_level
    : ap.approved_by_manager
    ? 'Đã Phê duyệt'
    : 'NVKD Tự quyết';
  document.getElementById('coralCardSub').textContent = `Phụ trách: ${item.assigned_rep.ho_ten} • SLA: ${ap.sla_hours}h`;

  const actionBox = document.getElementById('coralCardActionBox');
  if (!item.is_info_complete) {
    actionBox.innerHTML = `
      <button onclick="scrollToElement('clarifyLoopBox')" class="w-full py-2.5 px-3 rounded-xl bg-[#f06449] hover:bg-orange-600 active:scale-95 text-white text-xs font-extrabold shadow-sm transition flex items-center justify-center gap-1.5">
        <i class="fa-solid fa-reply"></i> Nhập Thông tin KH Bổ sung
      </button>
    `;
  } else if (ap.requires_manager_approval) {
    actionBox.innerHTML = `
      <div class="flex items-center gap-2">
        <div class="flex items-center bg-white rounded-xl border border-slate-200 px-2.5 py-1.5">
          <span class="text-[10px] font-bold text-slate-400 mr-1">CK%:</span>
          <input type="number" step="0.5" id="approveDiscountInput" value="${item.financials.ap_dung_chiet_khau_pct}" class="w-12 text-xs font-extrabold text-center text-[#0d1226] focus:outline-none" />
        </div>
        <button onclick="triggerApprovalAction('${item.ma_yeu_cau}', 'approve')" class="flex-1 py-2.5 px-3 rounded-xl bg-[#0d1226] hover:bg-slate-800 active:scale-95 text-white text-xs font-extrabold shadow-sm transition flex items-center justify-center gap-1.5">
          <i class="fa-solid fa-check-double text-[#f5b027]"></i> Duyệt Hồ sơ Ngay
        </button>
      </div>
    `;
  } else {
    actionBox.innerHTML = `
      <button onclick="scrollToElement('draftResponseSection')" class="w-full py-2.5 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white text-xs font-extrabold shadow-sm transition flex items-center justify-center gap-1.5">
        <i class="fa-solid fa-paper-plane"></i> Xem & Sao chép Báo giá Gửi KH
      </button>
    `;
  }

  // Card 3: 2x3 Metric Grid ("Sales Details")
  document.getElementById('gridMetric1').textContent = s.total_requests || 0;
  document.getElementById('gridMetric2').textContent = s.complete_count || 0;
  document.getElementById('gridMetric3').textContent = s.need_clarify_count || 0;
  document.getElementById('gridMetric4').textContent = s.need_manager_count || 0;
  document.getElementById('gridMetric5').textContent = `${item.operations.so_hang_muc} SP`;
  document.getElementById('gridMetric6').textContent = item.is_info_complete
    ? `${item.operations.thoi_gian_dap_ung_thuc_te_ngay} ngày`
    : 'Chờ chốt';
}

// ============================================================================
// 2. RENDER TOP HERO CARD (SMOOTH DUAL AREA WAVE CHART + 7-STEP WORKFLOW)
// ============================================================================
function renderTopHeroCard() {
  const chartContainer = document.getElementById('topHeroChartContainer');
  const wfContainer = document.getElementById('topHeroWorkflowContainer');
  const list = appData.results || [];
  const selected = getSelectedItem();

  if (list.length === 0) {
    chartContainer.innerHTML = `<div class="p-8 text-center text-slate-400 text-xs">Chưa có dữ liệu</div>`;
    return;
  }

  const width = 840;
  const height = 240;
  const padLeft = 60;
  const padRight = 32;
  const padTop = 26;
  const padBottom = 36;
  const plotW = width - padLeft - padRight;
  const plotH = height - padTop - padBottom;

  const maxVal = Math.max(
    1400_000_000,
    ...list.map((r) => Math.max(r.financials.tong_sau_chiet_khau || 0, r.financials.ngan_sach_khach_hang || 0))
  );

  const stepX = list.length > 1 ? plotW / (list.length - 1) : plotW;

  const quotePts = list.map((r, i) => {
    const val = r.is_info_complete
      ? r.financials.tong_sau_chiet_khau
      : r.line_items.reduce((a, b) => a + b.don_gia_niem_yet, 0);
    const x = padLeft + i * stepX;
    const y = padTop + plotH - Math.min(1, val / maxVal) * plotH;
    return { x, y, val, r };
  });

  const budgetPts = list.map((r, i) => {
    const val = r.financials.ngan_sach_khach_hang || 0;
    const x = padLeft + i * stepX;
    const y = padTop + plotH - Math.min(1, val / maxVal) * plotH;
    return { x, y, val, r };
  });

  function buildSmoothAreaPath(pts, baselineY) {
    if (pts.length === 0) return { linePath: '', areaPath: '' };
    if (pts.length === 1) {
      return {
        linePath: `M ${pts[0].x} ${pts[0].y}`,
        areaPath: `M ${pts[0].x} ${baselineY} L ${pts[0].x} ${pts[0].y} L ${pts[0].x + 10} ${baselineY} Z`,
      };
    }
    let d = `M ${pts[0].x} ${pts[0].y}`;
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[i];
      const p1 = pts[i + 1];
      const cx1 = p0.x + (p1.x - p0.x) * 0.45;
      const cx2 = p1.x - (p1.x - p0.x) * 0.45;
      d += ` C ${cx1} ${p0.y}, ${cx2} ${p1.y}, ${p1.x} ${p1.y}`;
    }
    const linePath = d;
    const areaPath = `${d} L ${pts[pts.length - 1].x} ${baselineY} L ${pts[0].x} ${baselineY} Z`;
    return { linePath, areaPath };
  }

  const baseY = padTop + plotH;
  const quoteCurve = buildSmoothAreaPath(quotePts, baseY);
  const budgetCurve = buildSmoothAreaPath(budgetPts, baseY);

  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((t) => {
    const val = maxVal * t;
    const y = baseY - t * plotH;
    return { y, label: formatShortVND(val) };
  });

  const selIdx = Math.max(0, list.findIndex((r) => r.ma_yeu_cau === selectedRequestId));
  const selQuotePt = quotePts[selIdx] || quotePts[0];

  chartContainer.innerHTML = `
    <div class="relative w-full overflow-x-auto">
      <svg viewBox="0 0 ${width} ${height}" class="w-full h-[240px] select-none">
        <defs>
          <linearGradient id="amberGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#f5b027" stop-opacity="0.88" />
            <stop offset="100%" stop-color="#f5b027" stop-opacity="0.16" />
          </linearGradient>
          <linearGradient id="coralGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#f06449" stop-opacity="0.86" />
            <stop offset="100%" stop-color="#f06449" stop-opacity="0.2" />
          </linearGradient>
        </defs>

        <!-- Horizontal Grid Lines -->
        ${yTicks
          .map(
            (tk) => `
          <line x1="${padLeft}" y1="${tk.y}" x2="${width - padRight}" y2="${tk.y}" stroke="#f1f5f9" stroke-width="1.3" />
          <text x="${padLeft - 12}" y="${tk.y + 4}" text-anchor="end" fill="#94a3b8" font-size="10.5" font-weight="700">${tk.label}</text>
        `
          )
          .join('')}

        <!-- Amber Wave (Proposed Quote Value) -->
        <path d="${quoteCurve.areaPath}" fill="url(#amberGrad)" class="wave-area-animate" />
        <path d="${quoteCurve.linePath}" fill="none" stroke="#f5b027" stroke-width="3.2" class="wave-line-animate" />

        <!-- Coral Wave (Customer Approved Budget) -->
        <path d="${budgetCurve.areaPath}" fill="url(#coralGrad)" class="wave-area-animate" />
        <path d="${budgetCurve.linePath}" fill="none" stroke="#f06449" stroke-width="2.8" class="wave-line-animate" />

        <!-- Interactive Customer Nodes -->
        ${quotePts
          .map((pt, idx) => {
            const isSel = pt.r.ma_yeu_cau === selectedRequestId;
            const bPt = budgetPts[idx];
            return `
              <g class="cursor-pointer group" onclick="selectRequest('${pt.r.ma_yeu_cau}')">
                ${
                  isSel
                    ? `
                  <line x1="${pt.x}" y1="${padTop}" x2="${pt.x}" y2="${baseY}" stroke="#0d1226" stroke-dasharray="4 4" stroke-width="1.5" />
                  <circle cx="${pt.x}" cy="${pt.y}" r="12" fill="#f5b027" fill-opacity="0.25">
                    <animate attributeName="r" values="7;15;7" dur="1.8s" repeatCount="indefinite" />
                  </circle>
                `
                    : ''
                }
                <circle cx="${pt.x}" cy="${pt.y}" r="${isSel ? 7 : 4.5}" fill="#f5b027" stroke="#ffffff" stroke-width="2.5" />
                <circle cx="${bPt.x}" cy="${bPt.y}" r="${isSel ? 6 : 4}" fill="#f06449" stroke="#ffffff" stroke-width="2" />
                <text x="${pt.x}" y="${height - 10}" text-anchor="middle" fill="${
              isSel ? '#0d1226' : '#94a3b8'
            }" font-size="11" font-weight="${isSel ? '800' : '600'}">
                  ${pt.r.ma_yeu_cau.replace('YC-2026-', 'YC-')}
                </text>
              </g>
            `;
          })
          .join('')}
      </svg>

      <!-- Floating Callout Badge on Wave Chart for Selected Customer -->
      ${
        selected
          ? `
        <div class="mt-2 px-4 py-2.5 rounded-2xl bg-[#f4f5f9] flex flex-wrap items-center justify-between gap-2 text-xs">
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded-lg bg-[#0d1226] text-white font-extrabold text-[11px]">${selected.ma_yeu_cau}</span>
            <span class="font-bold text-[#0d1226]">${selected.ten_khach_hang}</span>
          </div>
          <div class="flex flex-wrap items-center gap-4">
            <span>Đề xuất (Sau CK): <b class="text-[#f5b027]">${selected.is_info_complete ? formatVND(selected.financials.tong_sau_chiet_khau) : 'Chờ chốt SL'}</b></span>
            <span>Ngân sách KH: <b class="text-[#f06449]">${selected.financials.ngan_sach_khach_hang > 0 ? formatVND(selected.financials.ngan_sach_khach_hang) : 'Chưa cung cấp'}</b></span>
          </div>
        </div>
      `
          : ''
      }
    </div>
  `;

  // Mode B: Interactive 7-Step Minh An Workflow Trace
  if (selected) {
    const infoOk = selected.is_info_complete;
    const mgrReq = selected.is_info_complete && selected.approval.requires_manager_approval;
    const op = selected.operations;
    const f = selected.financials;
    const ap = selected.approval;

    const hl = (stepNum) =>
      activeSimStep === stepNum ? 'ring-4 ring-[#f5b027] scale-105 bg-amber-50/90 transition-all duration-300' : '';

    wfContainer.innerHTML = `
      <div class="bg-[#f4f5f9] rounded-2xl p-4 space-y-3 text-xs">
        <div class="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <div class="p-3.5 rounded-2xl bg-white border-2 border-emerald-500 text-center shadow-sm ${hl(1)}">
            <div class="text-[10px] font-extrabold text-emerald-600 uppercase">Bước 1 • Bắt đầu</div>
            <div class="font-extrabold text-[#0d1226] mt-0.5">Tiếp nhận yêu cầu</div>
            <div class="text-[11px] text-slate-500 mt-0.5">${selected.kenh_tiep_nhan} (${selected.ma_yeu_cau})</div>
          </div>

          <div class="p-3.5 rounded-2xl bg-white border-2 border-blue-500 text-center shadow-sm ${hl(2)}">
            <div class="text-[10px] font-extrabold text-blue-600 uppercase">Bước 2 • AI Bóc tách</div>
            <div class="font-extrabold text-[#0d1226] mt-0.5">Phân loại & Kiểm tra TT</div>
            <div class="text-[11px] text-slate-500 mt-0.5">${op.so_hang_muc} SP • NS: ${f.ngan_sach_khach_hang > 0 ? formatShortVND(f.ngan_sach_khach_hang) : 'Chưa rõ'}</div>
          </div>

          <div class="p-3.5 rounded-2xl bg-white border-2 ${infoOk ? 'border-emerald-500' : 'border-[#f06449]'} text-center shadow-sm ${hl(3)}">
            <div class="text-[10px] font-extrabold uppercase ${infoOk ? 'text-emerald-600' : 'text-[#f06449]'}">Cổng Quyết định 1</div>
            <div class="font-extrabold text-[#0d1226] mt-0.5">Có đủ thông tin?</div>
            <span class="inline-block mt-1 px-2.5 py-0.5 rounded-full text-[10px] font-extrabold text-white ${infoOk ? 'bg-emerald-600' : 'bg-[#f06449]'}">
              ${infoOk ? 'CÓ → Tạo Hồ sơ' : 'KHÔNG → Hỏi lại KH'}
            </span>
          </div>

          <div class="p-3.5 rounded-2xl ${!infoOk ? 'bg-amber-50 border-2 border-[#f06449] step-glow-active' : 'bg-white/60 border border-slate-200 opacity-55'} text-center ${hl(4)}">
            <div class="text-[10px] font-extrabold uppercase text-[#f06449]">Nhánh Làm rõ</div>
            <div class="font-extrabold text-[#0d1226] mt-0.5">Yêu cầu KH bổ sung</div>
            <div class="text-[11px] text-slate-500 mt-0.5">${!infoOk ? `Thiếu ${selected.missing_reasons.length} TT • Có nháp hỏi` : 'Bỏ qua (Đủ TT)'}</div>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-4 gap-3 pt-2.5 border-t border-slate-200/80">
          <div class="p-3.5 rounded-2xl bg-white border border-slate-200 text-center shadow-sm ${hl(5)}">
            <div class="text-[10px] font-extrabold text-blue-600 uppercase">Bước 3 • Gắn Owner</div>
            <div class="font-extrabold text-[#0d1226] mt-0.5">${selected.ma_ho_so_co_hoi}</div>
            <div class="text-[11px] text-slate-500 mt-0.5">${selected.assigned_rep.ho_ten}</div>
          </div>

          <div class="p-3.5 rounded-2xl bg-white border-2 ${op.so_hang_muc_thieu_ton > 0 ? 'border-[#f06449]' : 'border-emerald-500'} text-center shadow-sm ${hl(6)}">
            <div class="text-[10px] font-extrabold text-indigo-600 uppercase">Bước 4 • Giá & Tồn kho</div>
            <div class="font-extrabold text-[#0d1226] mt-0.5">${op.so_hang_muc - op.so_hang_muc_thieu_ton}/${op.so_hang_muc} đủ tồn kho</div>
            <div class="text-[11px] text-slate-500 mt-0.5">Đáp ứng: ${op.thoi_gian_dap_ung_thuc_te_ngay} ngày</div>
          </div>

          <div class="p-3.5 rounded-2xl bg-white border-2 ${mgrReq ? 'border-purple-600 step-glow-active' : 'border-emerald-500'} text-center shadow-sm ${hl(7)}">
            <div class="text-[10px] font-extrabold text-purple-600 uppercase">Cổng Quyết định 2</div>
            <div class="font-extrabold text-[#0d1226] mt-0.5">${mgrReq ? ap.approval_level : 'Trong thẩm quyền NVKD'}</div>
            <div class="text-[11px] text-slate-500 mt-0.5">Chính sách ${ap.policy_code}</div>
          </div>

          <div class="p-3.5 rounded-2xl bg-[#0d1226] text-white text-center shadow-md ${hl(8)}">
            <div class="text-[10px] font-extrabold text-[#f5b027] uppercase">Kết thúc • SLA ${ap.sla_hours}h</div>
            <div class="font-extrabold mt-0.5">${selected.final_status}</div>
            <div class="text-[11px] text-slate-300 mt-0.5">Cập nhật & Theo dõi</div>
          </div>
        </div>
      </div>
    `;
  }
}

// ============================================================================
// 3. RENDER BOTTOM-LEFT CARD ("Earning Details" style -> Chi tiết Báo giá)
// ============================================================================
function renderMiniDetailCard() {
  const item = getSelectedItem();
  const body = document.getElementById('miniDetailCardBody');
  const footer = document.getElementById('miniDetailFooterMetrics');
  if (!item || !body) return;

  const f = item.financials;
  const op = item.operations;

  footer.innerHTML = `
    <div>
      <div class="text-xs sm:text-sm font-extrabold text-[#0d1226]">${formatShortVND(f.tong_gia_niem_yet)}</div>
      <div class="text-[11px] text-slate-400 font-medium">giá niêm yết</div>
    </div>
    <div>
      <div class="text-xs sm:text-sm font-extrabold text-[#0d1226]">${formatShortVND(f.tong_sau_chiet_khau)}</div>
      <div class="text-[11px] text-slate-400 font-medium">sau chiết khấu</div>
    </div>
    <div>
      <div class="text-xs sm:text-sm font-extrabold ${f.is_within_budget ? 'text-emerald-600' : 'text-[#f06449]'}">
        ${f.ngan_sach_khach_hang > 0 ? formatShortVND(f.ngan_sach_khach_hang) : 'Chưa rõ'}
      </div>
      <div class="text-[11px] text-slate-400 font-medium">ngân sách KH</div>
    </div>
  `;

  if (miniDetailTab === 'fin') {
    body.innerHTML = `
      <div class="mb-2 panel-pop">
        <div class="text-2xl sm:text-3xl font-extrabold text-[#0d1226] tracking-tight">
          ${item.is_info_complete ? formatVND(f.tong_sau_chiet_khau) : 'Chờ KH Chốt SL'}
        </div>
        <div class="text-xs text-slate-400 mt-0.5 font-medium">
          ${item.ten_khach_hang} • CK: <b class="text-[#0d1226]">${f.ap_dung_chiet_khau_pct}% (-${formatShortVND(f.tien_chiet_khau)})</b>
        </div>
      </div>

      <!-- Smooth Amber Sparkline with Callout Tooltip matching "Earning Details" -->
      <div class="relative py-3">
        <svg viewBox="0 0 360 115" class="w-full h-[110px] overflow-visible">
          <path
            d="M 5 90 C 45 25, 85 25, 125 65 C 165 105, 200 35, 240 50 C 280 65, 315 95, 355 20"
            fill="none"
            stroke="#f5b027"
            stroke-width="2.8"
            class="wave-line-animate"
          />
          <line x1="205" y1="52" x2="205" y2="110" stroke="#f5b027" stroke-dasharray="3 3" stroke-width="1.5" />
          <circle cx="205" cy="52" r="6" fill="#f5b027" stroke="#ffffff" stroke-width="2.5" />
        </svg>
        <div class="absolute left-[42%] top-2 bg-white shadow-lg rounded-2xl px-3.5 py-2 border border-slate-100 text-xs">
          <div class="text-[10px] text-slate-400 font-bold">${item.ma_ho_so_co_hoi}</div>
          <div class="font-extrabold text-[#0d1226]">${op.so_hang_muc} Hạng mục • ${op.thoi_gian_dap_ung_thuc_te_ngay} ngày</div>
        </div>
      </div>
    `;
  } else if (miniDetailTab === 'guard') {
    body.innerHTML = `
      <div class="space-y-2 py-1 max-h-[195px] overflow-y-auto custom-scroll pr-1 panel-pop">
        ${item.guardrails
          .map(
            (g) => `
          <div class="p-2.5 rounded-xl bg-[#f4f5f9] flex items-start justify-between gap-2 text-xs">
            <div>
              <div class="font-bold text-[#0d1226]">${g.tieu_chi}</div>
              <div class="text-[11px] text-slate-500 leading-snug mt-0.5">${g.mo_ta}</div>
            </div>
            <span class="px-2 py-0.5 rounded-lg text-[10px] font-extrabold shrink-0 ${
              g.loai === 'success'
                ? 'bg-emerald-100 text-emerald-700'
                : g.loai === 'danger'
                ? 'bg-rose-100 text-rose-700'
                : 'bg-amber-100 text-amber-800'
            }">${g.trang_thai}</span>
          </div>
        `
          )
          .join('')}
      </div>
    `;
  } else {
    body.innerHTML = `
      <div class="space-y-2 py-1 max-h-[195px] overflow-y-auto custom-scroll pr-1 panel-pop">
        ${item.line_items
          .map(
            (li) => `
          <div class="p-2.5 rounded-xl bg-[#f4f5f9] flex items-center justify-between gap-2 text-xs">
            <div class="truncate">
              <div class="font-bold text-[#0d1226] truncate">[${li.ma_sp}] ${li.ten_sp}</div>
              <div class="text-[11px] text-slate-500">Yêu cầu: <b>${li.so_luong} ${li.ro_so_luong ? li.don_vi : ''}</b> • Tồn kho: <b>${li.ton_kha_dung}</b></div>
            </div>
            <span class="px-2 py-0.5 rounded-lg text-[10px] font-extrabold shrink-0 ${
              li.du_ton_kho ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
            }">
              ${li.du_ton_kho ? `${li.tg_dap_ung_ngay} ngày` : `Thiếu ${li.so_luong_thieu}`}
            </span>
          </div>
        `
          )
          .join('')}
      </div>
    `;
  }
}

// ============================================================================
// 4. RENDER BOTTOM-RIGHT CARD ("Recent Orders" style -> Danh sách Yêu cầu)
// ============================================================================
function setQueueFilter(filter) {
  currentFilter = filter;
  ['all', 'complete', 'clarify', 'manager'].forEach((f) => {
    const btn = document.getElementById(`filter-${f}`);
    if (!btn) return;
    if (f === filter) {
      btn.className = 'px-2.5 py-1 rounded-lg bg-[#0d1226] text-white shadow-sm transition';
    } else {
      btn.className = 'px-2.5 py-1 rounded-lg text-slate-500 hover:text-slate-900 transition';
    }
  });
  renderRecentOrdersCard();
}

function getFilteredResults() {
  return (appData.results || []).filter((r) => {
    if (currentFilter === 'complete' && !r.is_info_complete) return false;
    if (currentFilter === 'clarify' && r.is_info_complete) return false;
    if (currentFilter === 'manager' && (!r.is_info_complete || !r.approval.requires_manager_approval)) return false;

    if (searchQuery) {
      const hay = `${r.ma_yeu_cau} ${r.ma_ho_so_co_hoi} ${r.ten_khach_hang} ${r.nguoi_lien_he} ${r.noi_dung_yeu_cau} ${r.assigned_rep.ho_ten}`.toLowerCase();
      if (!hay.includes(searchQuery)) return false;
    }
    return true;
  });
}

function renderRecentOrdersCard() {
  const container = document.getElementById('recentOrdersContainer');
  if (!container) return;
  const list = getFilteredResults();

  if (list.length === 0) {
    container.innerHTML = `<div class="p-8 text-center text-slate-400 text-xs">Không tìm thấy yêu cầu khách hàng phù hợp.</div>`;
    return;
  }

  container.innerHTML = list
    .map((item, idx) => {
      const isSelected = item.ma_yeu_cau === selectedRequestId;
      const avatarGrad = AVATAR_COLORS[idx % AVATAR_COLORS.length];
      const initials = getInitials(item.ten_khach_hang);

      let statusBadge = '';
      if (!item.is_info_complete) {
        statusBadge = `<span class="px-2.5 py-1 rounded-lg bg-rose-100 text-[#f06449] text-[10px] font-extrabold uppercase">LÀM RÕ</span>`;
      } else if (item.approval.requires_manager_approval) {
        statusBadge = `<span class="px-2.5 py-1 rounded-lg bg-slate-200 text-slate-700 text-[10px] font-extrabold uppercase">CHỜ DUYỆT</span>`;
      } else {
        statusBadge = `<span class="px-2.5 py-1 rounded-lg bg-emerald-100 text-emerald-700 text-[10px] font-extrabold uppercase">SẴN SÀNG</span>`;
      }

      return `
        <div
          onclick="selectRequest('${item.ma_yeu_cau}')"
          class="order-row grid grid-cols-12 gap-2 items-center px-3 py-3 cursor-pointer ${
            isSelected ? 'selected' : ''
          }"
        >
          <div class="col-span-5 flex items-center gap-3 min-w-0">
            <div class="w-9 h-9 rounded-full bg-gradient-to-tr ${avatarGrad} text-white font-extrabold text-xs flex items-center justify-center shrink-0 shadow-sm">
              ${initials}
            </div>
            <div class="min-w-0">
              <div class="font-bold text-xs text-[#0d1226] truncate">${item.ten_khach_hang}</div>
              <div class="text-[11px] text-slate-400 truncate">NVKD: ${item.assigned_rep.ho_ten}</div>
            </div>
          </div>

          <div class="col-span-2 text-xs font-bold text-slate-600">
            #${item.ma_yeu_cau.replace('YC-2026-', '')}
          </div>

          <div class="col-span-3 text-right text-xs font-extrabold text-emerald-600">
            ${item.is_info_complete ? formatShortVND(item.financials.tong_sau_chiet_khau) : 'Chờ chốt SL'}
          </div>

          <div class="col-span-2 text-right">
            ${statusBadge}
          </div>
        </div>
      `;
    })
    .join('');
}

function selectRequest(id) {
  selectedRequestId = id;
  renderQuickCustomerChips();
  renderRightColumnCards();
  renderTopHeroCard();
  renderMiniDetailCard();
  renderRecentOrdersCard();
  renderDeepDiveWorkspace();
}

function scrollToElement(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// ============================================================================
// 5. RENDER DEEP-DIVE WORKSPACE BELOW OVERVIEW (TABLE, AI STRATEGY, EMAIL DRAFT)
// ============================================================================
function renderDeepDiveWorkspace() {
  const container = document.getElementById('activeOpportunityDeepDive');
  const item = getSelectedItem();
  if (!container || !item) return;

  const f = item.financials;
  const op = item.operations;
  const ap = item.approval;

  container.innerHTML = `
    <div class="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start panel-pop">

      <!-- LEFT 7 COLS: RAW REQUEST + PRODUCT AUDIT TABLE + AI RECOMMENDATIONS -->
      <div class="xl:col-span-7 space-y-6">

        <div class="bento-card p-6 space-y-4">
          <div class="flex flex-wrap items-start justify-between gap-2">
            <div>
              <div class="flex items-center gap-2">
                <span class="px-2.5 py-0.5 rounded-lg bg-[#0d1226] text-white text-xs font-extrabold">${item.ma_ho_so_co_hoi}</span>
                <span class="text-xs text-slate-400 font-semibold">${item.kenh_tiep_nhan} • ${item.ngay_nhan}</span>
              </div>
              <h3 class="text-base font-extrabold text-[#0d1226] mt-1">${item.ten_khach_hang} — ${item.nguoi_lien_he}</h3>
            </div>
            <span class="px-3 py-1 rounded-full text-xs font-extrabold ${
              !item.is_info_complete
                ? 'bg-rose-100 text-[#f06449]'
                : ap.requires_manager_approval
                ? 'bg-purple-100 text-purple-800'
                : 'bg-emerald-100 text-emerald-700'
            }">${item.final_status}</span>
          </div>

          <div class="p-4 rounded-2xl bg-[#f4f5f9] text-xs text-slate-700 leading-relaxed">
            <div class="text-[11px] font-extrabold text-slate-400 uppercase mb-1">Nội dung yêu cầu khách hàng:</div>
            "${item.noi_dung_yeu_cau}"
          </div>

          ${
            !item.is_info_complete
              ? `
            <div id="clarifyLoopBox" class="p-4 rounded-2xl bg-amber-50 border border-amber-200 space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-xs font-extrabold text-amber-950">
                  <i class="fa-solid fa-rotate text-[#f06449] mr-1"></i>Vòng lặp KH Bổ sung Thông tin (Nhánh Không → Quay lại Tiếp nhận):
                </span>
                <button type="button" onclick="autoFillClarification('${item.ma_yeu_cau}')" class="text-[11px] px-2.5 py-1 rounded-lg bg-white text-[#0d1226] font-extrabold shadow-sm hover:bg-amber-100 transition">
                  Điền mẫu KH phản hồi
                </button>
              </div>
              <ul class="list-disc list-inside text-xs text-amber-900 space-y-0.5">
                ${item.missing_reasons.map((r) => `<li>${r}</li>`).join('')}
              </ul>
              <div class="grid grid-cols-1 sm:grid-cols-4 gap-2 text-xs">
                <input type="text" id="clarifyTextInput" placeholder="Số lượng SP bổ sung..." class="sm:col-span-2 px-3 py-2 rounded-xl border border-amber-300 bg-white" />
                <input type="number" id="clarifyBudgetInput" placeholder="Ngân sách (VNĐ)" value="${f.ngan_sach_khach_hang > 0 ? f.ngan_sach_khach_hang : ''}" class="px-3 py-2 rounded-xl border border-amber-300 bg-white" />
                <div class="flex gap-1.5">
                  <input type="number" id="clarifyDeadlineInput" placeholder="Ngày" value="${op.thoi_han_khach_yeu_cau_ngay > 0 ? op.thoi_han_khach_yeu_cau_ngay : ''}" class="w-16 px-2 py-2 rounded-xl border border-amber-300 bg-white" />
                  <button onclick="submitClarification('${item.ma_yeu_cau}')" class="flex-1 px-3 py-2 rounded-xl bg-[#0d1226] text-white font-extrabold whitespace-nowrap">
                    Cập nhật
                  </button>
                </div>
              </div>
            </div>
            `
              : ''
          }

          <!-- Line Item Product, Price 2026 & Stock Table -->
          <div>
            <h4 class="text-xs font-extrabold uppercase tracking-wider text-slate-400 mb-2.5">
              Bảng Thẩm định Hạng mục Sản phẩm, Đơn giá 2026 & Tồn kho Khả dụng
            </h4>
            <div class="overflow-x-auto">
              <table class="w-full text-left border-collapse text-xs">
                <thead>
                  <tr class="bg-[#f4f5f9] text-slate-600 font-bold">
                    <th class="p-2.5 rounded-l-xl">Sản phẩm / Dịch vụ</th>
                    <th class="p-2.5 text-center">SL</th>
                    <th class="p-2.5 text-right">Đơn giá 2026</th>
                    <th class="p-2.5 text-right">Thành tiền</th>
                    <th class="p-2.5 text-center">Tồn kho</th>
                    <th class="p-2.5 text-center rounded-r-xl">Tiến độ</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                  ${item.line_items
                    .map(
                      (li) => `
                    <tr class="hover:bg-slate-50/80 transition">
                      <td class="p-2.5">
                        <div class="font-bold text-[#0d1226]">[${li.ma_sp}] ${li.ten_sp}</div>
                        <div class="text-[11px] text-slate-400">Giá cũ: ${formatVND(li.gia_cu_tham_chieu)} • BH: ${li.bao_hanh}</div>
                      </td>
                      <td class="p-2.5 text-center font-extrabold">${li.so_luong}</td>
                      <td class="p-2.5 text-right font-semibold">${formatShortVND(li.don_gia_niem_yet)}</td>
                      <td class="p-2.5 text-right font-extrabold text-[#0d1226]">${li.ro_so_luong ? formatShortVND(li.thanh_tien) : 'Chờ SL'}</td>
                      <td class="p-2.5 text-center">
                        <span class="px-2 py-0.5 rounded-lg text-[10px] font-extrabold ${
                          li.du_ton_kho ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-[#f06449]'
                        }">
                          ${li.du_ton_kho ? `Đủ (${li.ton_kha_dung})` : `Thiếu ${li.so_luong_thieu}`}
                        </span>
                      </td>
                      <td class="p-2.5 text-center font-bold">${li.tg_dap_ung_ngay} ngày</td>
                    </tr>
                  `
                    )
                    .join('')}
                </tbody>
              </table>
            </div>
          </div>

          <!-- AI Business Recommendations -->
          <div class="pt-2">
            <h4 class="text-xs font-extrabold uppercase tracking-wider text-slate-400 mb-2.5">
              Phân tích & Đề xuất Kinh doanh từ AI Agent
            </h4>
            <div class="space-y-2">
              ${item.recommendations
                .map(
                  (rec) => `
                <div class="p-3.5 rounded-2xl bg-[#f4f5f9] flex flex-col gap-1">
                  <div class="flex items-center justify-between">
                    <span class="font-extrabold text-xs text-[#0d1226]">${rec.nhom}</span>
                    <span class="text-[10px] px-2.5 py-0.5 rounded-lg bg-amber-100 text-amber-900 font-extrabold">${rec.muc_do}</span>
                  </div>
                  <p class="text-xs text-slate-600 leading-relaxed">${rec.noi_dung}</p>
                </div>
              `
                )
                .join('')}
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT 5 COLS: EDITABLE CUSTOMER RESPONSE EMAIL DRAFT -->
      <div id="draftResponseSection" class="xl:col-span-5 bento-card p-6 flex flex-col justify-between">
        <div>
          <div class="flex flex-wrap items-center justify-between gap-2 mb-3">
            <div>
              <h3 class="font-extrabold text-base text-[#0d1226]">Bản nháp Phản hồi Khách hàng</h3>
              <p class="text-xs text-slate-400">
                ${item.is_info_complete ? 'Đề xuất Kỹ thuật & Báo giá Thương mại chuẩn 2026' : 'Email đề nghị Khách hàng làm rõ thông tin kèm giá tham khảo'}
              </p>
            </div>
            <div class="flex items-center gap-2">
              <button onclick="copyDraftEmail()" class="px-3.5 py-2 rounded-xl bg-[#f5b027] hover:bg-amber-500 active:scale-95 text-white text-xs font-extrabold shadow-sm transition flex items-center gap-1.5">
                <i class="fa-regular fa-copy"></i> Sao chép
              </button>
              <button onclick="exportOpportunityDossier()" class="px-3.5 py-2 rounded-xl bg-[#0d1226] hover:bg-slate-800 active:scale-95 text-white text-xs font-extrabold shadow-sm transition flex items-center gap-1.5">
                <i class="fa-solid fa-download"></i> Tải .TXT
              </button>
            </div>
          </div>

          <textarea
            id="draftEmailTextarea"
            rows="22"
            class="w-full p-4 rounded-2xl bg-[#0d1226] text-slate-100 font-mono text-xs leading-relaxed border border-slate-800 focus:outline-none focus:ring-2 focus:ring-[#f5b027] custom-scroll"
          >${item.draft_email}</textarea>
        </div>
      </div>

    </div>
  `;
}

// ============================================================================
// 6. CATALOG, POLICIES & ACTIONS
// ============================================================================
function renderCatalogAndPolicies() {
  const catBody = document.getElementById('catalogTableBody');
  if (catBody && appData.catalog) {
    catBody.innerHTML = appData.catalog
      .map(
        (p) => `
      <tr class="hover:bg-slate-50">
        <td class="p-3.5 font-bold text-[#0d1226]">${p.ma_sp}</td>
        <td class="p-3.5 font-medium text-slate-800">${p.ten_sp}</td>
        <td class="p-3.5 text-slate-500">${p.nhom_sp}</td>
        <td class="p-3.5 text-right text-slate-400 line-through">${formatVND(p.gia_cu_tham_chieu)}</td>
        <td class="p-3.5 text-right font-extrabold text-[#0d1226]">${formatVND(p.don_gia_niem_yet)}</td>
        <td class="p-3.5 text-center font-bold text-emerald-600">${p.ton_kha_dung} ${p.don_vi}</td>
        <td class="p-3.5 text-center">${p.tg_trien_khai_co_san_ngay} ngày</td>
        <td class="p-3.5 text-center text-[#f06449] font-semibold">${p.tg_nhap_them_ngay} ngày</td>
        <td class="p-3.5 text-center font-bold">${p.chiet_khau_nv_toi_da_pct}% / ${p.chiet_khau_tp_toi_da_pct}%</td>
      </tr>
    `
      )
      .join('');
  }

  const polBody = document.getElementById('policyTableBody');
  if (polBody && appData.policies) {
    polBody.innerHTML = appData.policies
      .map(
        (pol) => `
      <tr class="hover:bg-slate-50">
        <td class="p-3.5 font-bold text-[#f06449]">${pol.ma_chinh_sach}</td>
        <td class="p-3.5 font-bold text-[#0d1226]">${pol.cap_phe_duyet}</td>
        <td class="p-3.5 font-semibold text-slate-700">${pol.nguoi_phu_trach_duyet}</td>
        <td class="p-3.5 text-slate-600">${formatVND(pol.gia_tri_don_tu_vnd)} → ${
          pol.gia_tri_don_den_vnd > 10000000000 ? 'Trên 1 tỷ VNĐ' : formatVND(pol.gia_tri_don_den_vnd)
        }</td>
        <td class="p-3.5 text-center font-extrabold text-[#0d1226]">Tối đa ${pol.chiet_khau_toi_da_pct}%</td>
        <td class="p-3.5 text-slate-600">${pol.dieu_kien_ap_dung}</td>
        <td class="p-3.5 text-center font-bold text-emerald-600">${pol.sla_phan_hoi_gio} giờ</td>
      </tr>
    `
      )
      .join('');
  }

  const repsGrid = document.getElementById('repsGridContainer');
  if (repsGrid && appData.sales_reps) {
    repsGrid.innerHTML = appData.sales_reps
      .map(
        (rep, i) => `
      <div class="p-4 rounded-2xl bg-[#f4f5f9] flex items-center justify-between gap-3">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-gradient-to-tr ${AVATAR_COLORS[i % AVATAR_COLORS.length]} text-white font-bold text-xs flex items-center justify-center">
            ${getInitials(rep.ho_ten)}
          </div>
          <div>
            <div class="font-bold text-sm text-[#0d1226]">${rep.ho_ten} <span class="text-xs text-slate-400">(${rep.ma_nvkd})</span></div>
            <div class="text-xs text-slate-500">${rep.chuyen_mon}</div>
            <div class="text-[11px] text-slate-400">${rep.email}</div>
          </div>
        </div>
        <div class="text-right">
          <div class="text-[10px] text-slate-400 uppercase font-bold">Đang xử lý</div>
          <div class="text-lg font-extrabold text-[#0d1226]">${rep.so_co_hoi_dang_xu_ly}</div>
        </div>
      </div>
    `
      )
      .join('');
  }
}

async function handleFileUpload() {
  const input = document.getElementById('fileUploadInput');
  if (!input.files || input.files.length === 0) {
    showStatusAlert('Vui lòng chọn một file .csv hoặc .xlsx trước khi nhấn Phân tích File.', 'error');
    return;
  }
  const file = input.files[0];
  const formData = new FormData();
  formData.append('file', file);
  formData.append('llm_provider', llmConfig.provider);
  formData.append('llm_api_key', llmConfig.api_key);

  toggleModal('uploadCenterModal');
  try {
    showStatusAlert(`Đang tải lên và phân tích file "${file.name}"...`, 'info');
    const res = await fetch('/api/upload-file', {
      method: 'POST',
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Lỗi tải file');
    updateUIWithData(data);
    showStatusAlert(
      `Đã nạp thành công file "${file.name}" — Tổng số: ${data.results.length} yêu cầu khách hàng.`,
      'success'
    );
  } catch (err) {
    showStatusAlert(err.message, 'error');
  }
}

async function handleGoogleSheetLoad() {
  const url = document.getElementById('googleSheetInput').value.trim();
  if (!url) {
    showStatusAlert('Vui lòng dán đường dẫn Google Sheet trước khi nhấn Nạp Google Sheet.', 'error');
    return;
  }
  toggleModal('uploadCenterModal');
  try {
    showStatusAlert('Đang kết nối và đồng bộ dữ liệu từ Google Sheets...', 'info');
    const res = await fetch('/api/load-google-sheet', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sheet_url: url,
        llm_provider: llmConfig.provider,
        llm_api_key: llmConfig.api_key,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Không thể tải Google Sheet');
    updateUIWithData(data);
    showStatusAlert(`Đã đồng bộ thành công từ Google Sheet (${data.results.length} yêu cầu).`, 'success');
  } catch (err) {
    showStatusAlert(err.message, 'error');
  }
}

function autoFillClarification(maYeuCau) {
  const txt = document.getElementById('clarifyTextInput');
  const bdg = document.getElementById('clarifyBudgetInput');
  const dl = document.getElementById('clarifyDeadlineInput');
  if (maYeuCau === 'YC-2026-004') {
    if (txt) txt.value = 'Chốt số lượng 10 bộ máy tính để bàn HP Pro Tower 400 G9, 01 bộ hội nghị truyền hình Logitech Rally Bar và 08 bộ phát Wifi Aruba AP22, đề nghị chiết khấu 5%';
    if (bdg) bdg.value = 310000000;
    if (dl) dl.value = 6;
  } else {
    if (txt) txt.value = 'Chốt số lượng 25 bộ phát Wifi Aruba AP22, 03 chiếc Switch Cisco C9200L 24P và 01 gói dịch vụ bảo trì 24/7';
    if (bdg) bdg.value = 320000000;
    if (dl) dl.value = 5;
  }
}

async function submitClarification(maYeuCau) {
  const textVal = document.getElementById('clarifyTextInput')?.value || '';
  const budgetVal = Number(document.getElementById('clarifyBudgetInput')?.value || 0);
  const deadlineVal = Number(document.getElementById('clarifyDeadlineInput')?.value || 0);

  try {
    showStatusAlert(`Đang cập nhật thông tin KH bổ sung cho ${maYeuCau} và chạy lại quy trình...`, 'info');
    const res = await fetch('/api/clarify-request', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ma_yeu_cau: maYeuCau,
        bo_sung_noi_dung: textVal,
        ngan_sach_vnd: budgetVal,
        thoi_han_yeu_cau_ngay: deadlineVal,
        llm_provider: llmConfig.provider,
        llm_api_key: llmConfig.api_key,
      }),
    });
    const data = await res.json();
    updateUIWithData(data, maYeuCau);
    showStatusAlert(`Đã bổ sung thông tin cho ${maYeuCau} — Hồ sơ đã chuyển sang lập Báo giá chính thức!`, 'success');
  } catch (err) {
    showStatusAlert('Lỗi cập nhật: ' + err.message, 'error');
  }
}

async function triggerApprovalAction(maYeuCau, action) {
  const discInput = document.getElementById('approveDiscountInput');
  const approvedDiscount = discInput ? Number(discInput.value) : null;
  try {
    showStatusAlert(`Đang cập nhật phê duyệt cho hồ sơ ${maYeuCau}...`, 'info');
    const res = await fetch('/api/approve-action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ma_yeu_cau: maYeuCau,
        action: action,
        approved_discount_pct: approvedDiscount,
        approver_note: `Đã duyệt mức chiết khấu ${approvedDiscount}% và phương án triển khai.`,
      }),
    });
    const data = await res.json();
    updateUIWithData(data, maYeuCau);
    showStatusAlert(`Hồ sơ ${maYeuCau} đã được phê duyệt thành công!`, 'success');
  } catch (err) {
    showStatusAlert('Lỗi phê duyệt: ' + err.message, 'error');
  }
}

function fillPresetRequest(presetNum) {
  if (presetNum === 1) {
    document.getElementById('newReqCompany').value = 'Công ty Cổ phần Sản xuất Điện tử Việt Nhật';
    document.getElementById('newReqContact').value = 'Anh Phạm Quốc Khánh - Trưởng phòng Mua hàng';
    document.getElementById('newReqEmail').value = 'khanh.pq@vietnhat-elec.vn';
    document.getElementById('newReqContent').value =
      'Chào Minh An, nhà máy bên mình cần báo giá 05 bộ Máy chủ Dell PowerEdge R760xs, 08 chiếc Switch Cisco C9200L 24P, 02 bộ Tường lửa FortiGate 100F và 01 gói dịch vụ triển khai cấu hình hạ tầng mạng. Ngân sách tổng được duyệt là 1.150.000.000 VNĐ, đề nghị chiết khấu 9%. Yêu cầu triển khai bàn giao trong 7 ngày.';
  } else {
    document.getElementById('newReqCompany').value = 'Công ty TNHH Chuỗi Bán lẻ MegaMart';
    document.getElementById('newReqContact').value = 'Chị Bùi Thu Trang - Quản lý Dự án';
    document.getElementById('newReqEmail').value = 'trang.bt@megamart.vn';
    document.getElementById('newReqContent').value =
      'Chào Minh An, bên mình sắp khai trương văn phòng điều hành mới nên cần mua một số chiếc Laptop Dell Latitude 5440, hệ thống lưu trữ Synology NAS RS1221+ và khoảng 12 bộ phát Wifi Aruba AP22. Bên mình chưa chốt số lượng laptop và ngân sách tổng, nhờ Minh An gửi đơn giá trước nhé.';
  }
}

async function submitNewRequest() {
  const payload = {
    ten_khach_hang: document.getElementById('newReqCompany').value.trim(),
    nguoi_lien_he: document.getElementById('newReqContact').value.trim(),
    email_kh: document.getElementById('newReqEmail').value.trim(),
    kenh_tiep_nhan: document.getElementById('newReqChannel').value,
    noi_dung_yeu_cau: document.getElementById('newReqContent').value.trim(),
    ngan_sach_vnd: Number(document.getElementById('newReqBudget').value || 0),
    thoi_han_yeu_cau_ngay: Number(document.getElementById('newReqDeadline').value || 0),
    de_nghi_chiet_khau_pct: Number(document.getElementById('newReqDiscount').value || 0),
    llm_provider: llmConfig.provider,
    llm_api_key: llmConfig.api_key,
  };

  if (!payload.ten_khach_hang || !payload.noi_dung_yeu_cau) {
    alert('Vui lòng nhập Tên khách hàng và Nội dung yêu cầu.');
    return;
  }

  toggleModal('newRequestModal');
  showStatusAlert('AI Agent đang bóc tách văn bản yêu cầu, đối chiếu giá 2026 & tồn kho...', 'info');

  try {
    const res = await fetch('/api/analyze-single', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    updateUIWithData(data, data.created_id);
    showStatusAlert(`Đã tiếp nhận & lập Hồ sơ phân tích cho yêu cầu mới (${data.created_id})!`, 'success');
  } catch (err) {
    showStatusAlert('Lỗi khi phân tích yêu cầu: ' + err.message, 'error');
  }
}

function saveAiConfig() {
  llmConfig.provider = document.getElementById('llmProviderSelect').value;
  llmConfig.api_key = document.getElementById('llmApiKeyInput').value.trim();
  toggleModal('aiConfigModal');
  fetchInitialData();
}

async function resetSampleData() {
  showStatusAlert('Đang khôi phục bộ dữ liệu mẫu gốc của Công ty Minh An...', 'info');
  const res = await fetch('/api/reset-sample', { method: 'POST' });
  const data = await res.json();
  selectedRequestId = null;
  updateUIWithData(data);
  showStatusAlert('Đã khôi phục 6 yêu cầu B2B mẫu chuẩn của Công ty Minh An.', 'success');
}

function copyDraftEmail() {
  const area = document.getElementById('draftEmailTextarea');
  if (!area) return;
  navigator.clipboard.writeText(area.value);
  showStatusAlert('Đã sao chép Bản nháp Phản hồi Khách hàng vào bộ nhớ tạm (Clipboard)!', 'success');
}

function exportOpportunityDossier() {
  const item = getSelectedItem();
  if (!item) return;
  const draftText = document.getElementById('draftEmailTextarea')?.value || item.draft_email;
  const content = [
    '====================================================================',
    `HỒ SƠ CƠ HỘI BÁN HÀNG B2B - CÔNG TY CÔNG NGHỆ MINH AN`,
    '====================================================================',
    `Mã Hồ sơ Cơ hội : ${item.ma_ho_so_co_hoi} (Từ Yêu cầu: ${item.ma_yeu_cau})`,
    `Khách hàng      : ${item.ten_khach_hang}`,
    `Người liên hệ   : ${item.nguoi_lien_he} (${item.email_kh})`,
    `Trạng thái      : ${item.final_status}`,
    `NVKD Phụ trách  : ${item.assigned_rep.ho_ten} (${item.assigned_rep.ma_nvkd})`,
    `Cấp Phê duyệt   : ${item.approval.approver_name}`,
    '',
    '--- KẾT QUẢ PHÂN TÍCH & ĐỀ XUẤT KINH DOANH ---',
    ...item.recommendations.map((r, i) => `${i + 1}. [${r.nhom} - ${r.muc_do}]: ${r.noi_dung}`),
    '',
    '--- BẢN NHÁP PHẢN HỒI KHÁCH HÀNG ---',
    draftText,
  ].join('\n');

  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${item.ma_ho_so_co_hoi}_${item.ma_yeu_cau}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

window.addEventListener('DOMContentLoaded', () => {
  fetchInitialData();
});
