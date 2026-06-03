var STATUS_COLORS = {
  "Ready for Plan": "#a855f7",
  "Planned": "#6366f1",
  "Executing": "#06b6d4",
  "Blocked": "#ef4444",
  "Decision Needed": "#f97316",
  "Review Needed": "#3b82f6",
  "Closed": "#22c55e",
  "Cancelled": "#64748b",
  "Unknown": "#94a3b8",
};

var PRIORITY_COLORS = {
  "P0": "#ef4444",
  "P1": "#f97316",
  "P2": "#eab308",
  "P3": "#22c55e",
};

var PRIORITY_NORMALIZE = {
  "urgent": "P0", "high": "P1", "important": "P1",
  "medium": "P2", "normal": "P2", "low": "P3",
  "P0": "P0", "P1": "P1", "P2": "P2", "P3": "P3",
};

function normalizePriority(raw) {
  if (!raw) return "";
  var r = String(raw).trim();
  return PRIORITY_NORMALIZE[r] || r;
}

var focusItemIcons = {blocked: "", waiting: "🟡", review: "🔵", executing: "", planned: ""};

var PROJECTS = {};
var PRODUCT = {};

var state = null;
var pmOverview = null;
var waitingDecisions = [];
var _reqData = null;
var _actionBoardData = null;
var _reqViewMode = "list";
var _reqProjectFilter = "";
var _memoProjectFilter = "";
var _memoViewMode = "kanban";
var _editingMemoId = null;
var _editingMemoProject = null;
var _archivingMemoId = null;
var _archivingMemoProject = null;
var _docViewMode = "raw";
var _currentDocPath = null;
var _currentDocContent = null;
var _reqSearchTimer = null;
var _memoSearchTimer = null;
var _autoRefreshTimer = null;
var _pendingTransition = null;
var _taskHealthData = null;
var _requirementOverviewData = null;
var _memoStats = null;
var _taskBaseData = null;
var _memoData = null;
var _expandedChangeId = null;

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"]/g, function(ch) {
    return {"&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;"}[ch];
  });
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/'/g, "&#39;");
}

var ALIAS = {
  status: {
    "Ready for Plan": "待规划",
    "Planned": "已规划",
    "Executing": "执行中",
    "Blocked": "已阻塞",
    "Decision Needed": "待决策",
    "Review Needed": "待验收",
    "Closed": "已完成",
    "Cancelled": "已取消",
    "Unknown": "未知"
  },
  decision: {
    "Accepted": "已确认",
    "Proposed": "提议中",
    "Superseded": "已废弃",
    "Deprecated": "已废弃"
  },
  priority: {
    "P0": "P0",
    "P1": "P1",
    "P2": "P2",
    "P3": "P3",
    "urgent": "P0",
    "high": "P1",
    "important": "P1",
    "medium": "P2",
    "normal": "P2",
    "low": "P3"
  },
  audit: {
    "pass": "通过",
    "warn": "警告",
    "fail": "失败"
  },
  severity: {
    "high": "高",
    "medium": "中",
    "low": "低"
  }
};

function alias(cat, val) {
  if (val === null || val === undefined) return "未知";
  var mapped = ALIAS[cat] && ALIAS[cat][val];
  if (mapped) return mapped;
  return String(val);
}

function emptyValue(value) {
  if (value === null || value === undefined || String(value).trim() === "") return "未写入事实源";
  return String(value);
}

function taskDetailTarget(context) {
  return document.getElementById("taskDetailBody");
}

function openTaskDetail(data) {
  var overlay = document.getElementById("taskDetailOverlay");
  var panel = document.getElementById("taskDetailPanel");
  if (!overlay || !panel) return;
  overlay.classList.add("open");
  panel.classList.add("open");
  renderTaskDetailPanel(data);
}

function closeTaskDetail() {
  var overlay = document.getElementById("taskDetailOverlay");
  var panel = document.getElementById("taskDetailPanel");
  if (overlay) overlay.classList.remove("open");
  if (panel) panel.classList.remove("open");
}

function copyTaskPrompt(btn) {
  var encoded = btn.getAttribute("data-copy");
  var text = decodeURIComponent(escape(atob(encoded)));
  function onSuccess() {
    var orig = btn.textContent;
    btn.textContent = "已复制";
    btn.classList.add("copied");
    setTimeout(function() { btn.textContent = orig; btn.classList.remove("copied"); }, 1500);
  }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(onSuccess).catch(function() {
      fallbackCopy(text, btn, onSuccess);
    });
  } else {
    fallbackCopy(text, btn, onSuccess);
  }
}

function fallbackCopy(text, btn, onSuccess) {
  var ta = document.createElement("textarea");
  ta.value = text;
  ta.style.cssText = "position:fixed;left:-9999px;top:-9999px;opacity:0;";
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  try { document.execCommand("copy"); onSuccess(); } catch(e) { alert("复制失败，请手动复制"); }
  document.body.removeChild(ta);
}

function setTab(name) {
  var legacyRoutes = {
    docs: function() { setTab("requirements"); openSourceDocsFromReq(); },
    memos: function() { setTab("actions"); loadTaskBaseFromActions(); },
    panorama: function() { setTab("settings"); setSettingsTab("panorama"); },
    projects: function() { setTab("settings"); setSettingsTab("productConfig"); },
    waitingDecisions: function() { setTab("governance"); setGovTab("waitingDecisions"); },
    rulesAudit: function() { setTab("governance"); setGovTab("rulesAudit"); },
    changes: function() { setTab("governance"); setGovTab("changes"); },
    requirementOverview: function() { setTab("requirements"); },
    requirementsBoard: function() { setTab("actions"); }
  };
  if (legacyRoutes[name]) { legacyRoutes[name](); return; }
  var sectionName = name === "tasks" ? "overview" : name;
  document.querySelectorAll("section").forEach(function(s) { s.classList.toggle("active", s.id === sectionName); });
  document.querySelectorAll("nav .tab").forEach(function(t) { t.classList.toggle("active", t.dataset.tab === name); });
  if (name === "governance") { setGovTab("waitingDecisions"); loadWaitingDecisions(); }
  if (name === "actions") loadRequirements();
  if (name === "requirements") loadRequirementOverview();
  if (name === "settings") setSettingsTab("projectRules");
  if (name === "product" || name === "overview" || name === "tasks") { loadPmOverview(); renderHealthBar(); renderTaskMetricsPreview(pmOverview ? pmOverview.summary : null); renderRequirementProgress(); renderRecentChanges(); }
}

// 治理区子 tab
function setGovTab(name) {
  var idMap = { waitingDecisions: "govWaitingDecisions", decisions: "govDecisions", rulesAudit: "govRulesAudit", changes: "govChanges" };
  document.querySelectorAll("#governance > [id^='gov']").forEach(function(el) { el.classList.toggle("hidden", el.id !== idMap[name]); });
  document.querySelectorAll("#governance .tab").forEach(function(t) { t.classList.toggle("active", t.dataset.govtab === name); });
  if (name === "waitingDecisions") loadWaitingDecisions();
  if (name === "decisions") loadDecisionsInGovernance();
  if (name === "rulesAudit") loadRulesAudit();
}

function loadDecisionsInGovernance() {
  var container = document.getElementById("govDecisionsList");
  if (!container || !state || !state.decisions) return;
  var decs = state.decisions;
  var bySource = {};
  decs.forEach(function(d) {
    var key = d.source + (d.source === "项目决策" ? " · " + (PROJECTS[d.project] ? PROJECTS[d.project].name : d.project) : "");
    if (!bySource[key]) bySource[key] = [];
    bySource[key].push(d);
  });
  var html = "";
  Object.keys(bySource).forEach(function(group) {
    var items = bySource[group];
    html += '<div style="margin-bottom:16px;">';
    html += '<div style="font-weight:600;font-size:14px;color:var(--text);margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid var(--border);">' + escapeHtml(group) + ' (' + items.length + ')</div>';
    html += '<table style="width:100%;border-collapse:collapse;font-size:13px;">';
    items.forEach(function(d) {
      var statusClass = d.status === "Accepted" || d.status === "已确认" || d.status === "已采纳" ? "done" : d.status === "Superseded" || d.status === "已废弃" || d.status === "已拒绝" || d.status === "Deprecated" ? "" : "next";
      html += '<tr style="border-bottom:1px solid var(--border);">';
      html += '<td style="padding:6px 8px;white-space:nowrap;width:80px;"><span class="pill ' + statusClass + '">' + escapeHtml(alias('decision', d.status)) + '</span></td>';
      html += '<td style="padding:6px 8px;">' + escapeHtml(d.title) + '</td>';
      html += '<td style="padding:6px 8px;color:var(--muted);white-space:nowrap;width:100px;text-align:right;">' + escapeHtml(d.date ? d.date.substring(0, 10) : "") + '</td>';
      html += '</tr>';
    });
    html += '</table></div>';
  });
  container.innerHTML = html || '<div style="color:var(--muted);padding:8px;">暂无决策记录</div>';
}

// 设置区子 tab
function setSettingsTab(name) {
  var idMap = { projectRules: "setProjectRules", productConfig: "setProductConfig", panorama: "setPanorama", about: "setAbout" };
  document.querySelectorAll("#settings > [id^='set']").forEach(function(el) { el.classList.toggle("hidden", el.id !== idMap[name]); });
  document.querySelectorAll("#settings .tab").forEach(function(t) { t.classList.toggle("active", t.dataset.settab === name); });
  if (name === "projectRules") loadProjectRules();
  if (name === "productConfig") loadProductConfig();
  if (name === "panorama") loadPanoramaInSettings();
}

function loadProjectRules() {
  if (state && state.project_rules) {
    document.getElementById("projectRules").innerHTML = state.project_rules.map(function(project) {
      return "<tr><td>" + escapeHtml(project.name || project.project) + "</td><td>" + escapeHtml(project.role || "") + "</td><td>" + (project.exists ? '<span class="pill done">存在</span>' : '<span class="pill" style="color:#fecaca;border-color:rgba(239,68,68,.5)">缺失</span>') + "</td><td>" + (project.has_docs_index ? '<span class="pill done">有</span>' : '<span class="pill">待补</span>') + "</td><td>" + (project.has_compression ? '<span class="pill done">有</span>' : '<span class="pill">待补</span>') + "</td></tr>";
    }).join("");
  }
}

function loadProductConfig() {
  document.getElementById("cfgProductId").textContent = PRODUCT.id || "-";
  document.getElementById("cfgProductName").textContent = PRODUCT.name || "-";
  document.getElementById("cfgProductDesc").textContent = PRODUCT.description || PRODUCT.desc || "-";
  var listEl = document.getElementById("cfgProjectList");
  if (listEl) {
    var html = "";
    Object.keys(PROJECTS).forEach(function(key) {
      var p = PROJECTS[key];
      html += '<div style="padding:10px 0;border-bottom:1px solid var(--border);">' +
        '<strong>' + escapeHtml(p.name) + '</strong> <span class="pill">' + escapeHtml(key) + '</span>' +
        '<p style="color:var(--muted);font-size:12px;margin-top:4px;">' + escapeHtml(p.role || "") + '</p>' +
        '</div>';
    });
    listEl.innerHTML = html || '<p style="color:var(--muted);">暂无项目配置</p>';
  }
}

function loadPanoramaInSettings() {
  loadPanorama();
}

function loadTaskBaseFromActions() {
  var area = document.getElementById("actionTaskBaseArea");
  if (area.classList.contains("hidden")) {
    area.classList.remove("hidden");
    loadTaskBase();
  } else {
    area.classList.add("hidden");
  }
}

function openSourceDocsFromReq() {
  var area = document.getElementById("reqDocViewArea");
  if (area.classList.contains("hidden")) {
    area.classList.remove("hidden");
    loadDocs();
  } else {
    area.classList.add("hidden");
  }
}

function openSourceDoc(path) {
  setTab("requirements");
  var area = document.getElementById("reqDocViewArea");
  area.classList.remove("hidden");
  setTimeout(function() { loadDoc(path); }, 0);
}

function navigateToTask(projectId, docId, taskId) {
  setTab("actions");
  setTimeout(function() { loadTaskDetail(projectId, docId, taskId, "waiting"); }, 200);
}

async function loadDocs() {
  try {
    var response = await fetch("/api/docs");
    if (!response.ok) throw new Error(await response.text());
    var data = await response.json();
    var container = document.getElementById("docList");
    if (container && data.docs) {
      container.innerHTML = data.docs.map(function(doc) {
        return '<div class="doc" onclick="loadDoc(\'' + escapeHtml(doc.path) + "')\"><strong>" + escapeHtml(doc.id || doc.path) + " · " + escapeHtml(doc.title || "") + "</strong><span>" + escapeHtml(doc.role || "") + " · " + escapeHtml(doc.path) + "</span></div>";
      }).join("");
    }
  } catch (error) {
    var container = document.getElementById("docList");
    if (container) container.innerHTML = '<div class="error">' + escapeHtml(error.message) + '</div>';
  }
}

function updateLastRefresh() {
  var el = document.getElementById("lastRefresh");
  if (!el) return;
  el.textContent = "上次刷新: " + new Date().toLocaleTimeString("zh-CN");
}

async function loadConfig() {
  try {
    var response = await fetch("/api/config");
    if (!response.ok) throw new Error(await response.text());
    var data = await response.json();
    PRODUCT = data.product || {};
    PROJECTS = data.projects || {};
    if (data.config_error) {
      var productEl = document.getElementById("healthBarProduct");
      var descriptionEl = document.getElementById("healthBarDescription");
      if (productEl) productEl.textContent = "PM Kit — 配置缺失";
      if (descriptionEl) descriptionEl.textContent = "请检查 product.yaml";
    } else {
      var productEl = document.getElementById("healthBarProduct");
      var descriptionEl = document.getElementById("healthBarDescription");
      if (productEl && PRODUCT.name) {
        productEl.textContent = PRODUCT.name;
      }
      if (descriptionEl && PRODUCT.description) {
        descriptionEl.textContent = PRODUCT.description;
      }
    }
    _populateProjectSelectors();
  } catch(e) {}
}

function _populateProjectSelectors() {
}

async function loadData(force) {
  var url = force ? "/api/refresh" : "/api/dashboard";
  var options = force ? {method: "POST"} : {};
  var response = await fetch(url, options);
  if (!response.ok) throw new Error(await response.text());
  var payload = await response.json();
  state = payload.dashboard || payload;
  await Promise.all([
    loadPmOverview(),
    loadTaskHealthSilent(),
    loadRequirementOverviewSilent(),
    loadMemoStatsSilent(),
    loadMemosSilent()
  ]);
  render();
  updateLastRefresh();
}

async function refreshData() {
  await loadData(true);
  if (_reqData) loadRequirements();
  if (_taskBaseData) loadTaskBase();
  renderHealthBar();
  renderTaskMetricsPreview(pmOverview ? pmOverview.summary : null);
}

function openApi() { window.open("/docs", "_blank"); }

async function loadPmOverview() {
  try {
    var response = await fetch("/api/pm/overview");
    if (!response.ok) throw new Error(await response.text());
    pmOverview = await response.json();
  } catch (error) {
    pmOverview = {error: error.message, summary: {}};
  }
}

async function loadTaskHealthSilent() {
  try {
    var response = await fetch("/api/pm/task-health");
    if (!response.ok) throw new Error(await response.text());
    _taskHealthData = await response.json();
  } catch (error) {
    _taskHealthData = null;
  }
}

async function loadRequirementOverviewSilent() {
  try {
    var response = await fetch("/api/pm/requirement-overview");
    if (!response.ok) throw new Error(await response.text());
    _requirementOverviewData = await response.json();
  } catch (error) {
    _requirementOverviewData = null;
  }
}

async function loadMemoStatsSilent() {
  try {
    var response = await fetch("/api/memos/stats");
    if (!response.ok) throw new Error(await response.text());
    var data = await response.json();
    _memoStats = data.stats || null;
  } catch (error) {
    _memoStats = null;
  }
}

async function loadMemosSilent() {
  try {
    var response = await fetch("/api/memos");
    if (!response.ok) throw new Error(await response.text());
    var data = await response.json();
    _memoData = data.memos || [];
  } catch (error) {
    _memoData = [];
  }
}

async function loadWaitingDecisions() {
  var summary = document.getElementById("waitingSummary");
  var list = document.getElementById("waitingList");
  if (summary) summary.innerHTML = '<div class="card"><p>加载中...</p></div>';
  if (list) list.innerHTML = "";
  try {
    var response = await fetch("/api/pm/waiting-decisions");
    if (!response.ok) throw new Error(await response.text());
    var data = await response.json();
    waitingDecisions = data.items || [];
    renderWaitingDecisions(waitingDecisions);
  } catch (error) {
    if (summary) summary.innerHTML = '<div class="error">' + escapeHtml(error.message) + '</div>';
  }
}

function renderWaitingDecisions(items) {
  var summary = document.getElementById("waitingSummary");
  var list = document.getElementById("waitingList");
  if (!summary || !list) return;
  var byStatus = {};
  items.forEach(function(item) { byStatus[item.normalized_status || item.status || "未知"] = (byStatus[item.normalized_status || item.status || "未知"] || 0) + 1; });
  summary.innerHTML =
    '<div class="card"><h3>待决策 <span style="font-size:10px;color:var(--dim);font-weight:normal;">需人类判断</span></h3><div class="metric" style="color:var(--orange)">' + (byStatus["Decision Needed"] || 0) + '</div></div>' +
    '<div class="card"><h3>待验收 <span style="font-size:10px;color:var(--dim);font-weight:normal;">做完了等确认</span></h3><div class="metric" style="color:#3b82f6">' + (byStatus["Review Needed"] || 0) + '</div></div>' +
    '<div class="card"><h3>计划确认</h3><div class="metric" style="color:var(--cyan)">' + (byStatus["Plan Review"] || 0) + '</div></div>' +
    '<div class="card"><h3>需澄清</h3><div class="metric" style="color:var(--orange)">' + (byStatus["Need Clarification"] || 0) + '</div></div>';
  if (items.length === 0) {
    list.innerHTML = '<div class="card" style="grid-column:1/-1;"><p style="color:var(--muted);">暂无等待决策事项。</p></div>';
    return;
  }
  list.innerHTML = items.map(function(item) {
    var projName = PROJECTS[item.project] ? PROJECTS[item.project].name : (item.project_name || item.project || "未知项目");
    var decisionText = item.decision_needed || item.decision_point || item.human_gate || item.block_reason || "未写入事实源";
    return '<div class="card">' +
      '<h3>' + escapeHtml(item.id) + ' · ' + escapeHtml(item.title) + '</h3>' +
      '<p><span class="pill current">' + escapeHtml(alias('status', item.normalized_status || item.status)) + '</span>' +
      (item.priority ? '<span class="pill">' + escapeHtml(alias('priority', item.priority)) + '</span>' : '') +
      (item.type ? '<span class="pill">' + escapeHtml(item.type) + '</span>' : '') + '</p>' +
      '<p style="margin-top:8px;"><b>需要决策：</b>' + escapeHtml(emptyValue(decisionText)) + '</p>' +
      '<p style="margin-top:8px;color:var(--dim);">来源：' + escapeHtml(projName) + ' / ' + escapeHtml(item.doc_id || "") + ' · ' + escapeHtml(item.doc_title || "") + '</p>' +
      '<div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;"><button class="btn primary" onclick="loadTaskDetail(\'' + escapeHtml(item.project || "") + '\',\'' + escapeHtml(item.doc_id || "") + '\',\'' + escapeHtml(item.id || "") + '\',\'waiting\')">查看详情</button><button class="btn" onclick="loadDoc(\'' + escapeHtml(item.path || "") + '\');setTab(\'docs\');">查看源文档</button></div>' +
      '</div>';
  }).join("");
}

function renderHealthBar() {
  var container = document.getElementById("healthBarMetrics");
  var productEl = document.getElementById("healthBarProduct");
  var descriptionEl = document.getElementById("healthBarDescription");
  if (!container) return;
  if (PRODUCT.name && productEl) {
    productEl.textContent = PRODUCT.name;
  }
  if (PRODUCT.description && descriptionEl) {
    descriptionEl.textContent = PRODUCT.description;
  }
  if (!pmOverview || !pmOverview.summary) {
    container.innerHTML = '<span style="color:var(--muted);font-size:13px;">加载中...</span>';
    return;
  }
  var s = pmOverview.summary;
  container.innerHTML =
    '<div class="health-metric hm-executing" onclick="setTab(\'product\')" title="正在执行中的任务"><span class="hm-count">' + (s.executing || 0) + '</span>进行中</div>' +
    '<div class="health-metric hm-planned" onclick="setTab(\'product\')" title="已规划但尚未开始的任务"><span class="hm-count">' + (s.planned || 0) + '</span>已规划</div>' +
    '<div class="health-metric hm-blocked" onclick="setTab(\'product\')" title="被外部因素卡住，无法继续"><span class="hm-count">' + (s.blocked || 0) + '</span>被阻塞</div>' +
    '<div class="health-metric hm-waiting" onclick="setTab(\'product\')" title="需要人类判断才能继续执行"><span class="hm-count">' + (s.decision_needed || 0) + '</span>待决策</div>' +
    '<div class="health-metric hm-review" onclick="setTab(\'product\')" title="执行完成，等待审计验收确认"><span class="hm-count">' + (s.review_needed || 0) + '</span>待验收</div>';
}

function renderTaskMetricsPreview(summary) {
  var container = document.getElementById("taskMetricsPreview");
  if (!container) return;
  var values = [
    {label: "进行中", value: summary.executing, color: STATUS_COLORS["Executing"]},
    {label: "已规划", value: summary.planned, color: STATUS_COLORS["Planned"]},
    {label: "待规划", value: summary.ready_for_plan, color: STATUS_COLORS["Ready for Plan"]},
    {label: "待决策", value: summary.decision_needed, color: STATUS_COLORS["Decision Needed"]},
    {label: "待验收", value: summary.review_needed, color: STATUS_COLORS["Review Needed"]},
    {label: "被阻塞", value: summary.blocked, color: STATUS_COLORS["Blocked"]}
  ];
  Array.prototype.forEach.call(container.querySelectorAll(".metric-card"), function(card, index) {
    var item = values[index];
    if (item) card.innerHTML = '<div class="metric-label">' + item.label + '</div><div class="metric-value" style="color:' + item.color + '">' + (item.value || 0) + '</div>';
  });
}

function renderMemoListOverview() {
  var container = document.querySelector("#memoListOverview .memo-list-content");
  if (!container) return;

  var memos = (_memoData || []).filter(function(m) { return m.status === "pending" || m.status === "open"; });
  var itemsHtml = '';
  if (memos.length > 0) {
    itemsHtml = memos.slice(0, 5).map(function(m) {
      var normPrio = normalizePriority(m.priority);
      var prioBg = normPrio ? (PRIORITY_COLORS[normPrio] || '#94a3b8') + '22' : 'transparent';
      var prioColor = normPrio ? (PRIORITY_COLORS[normPrio] || '#94a3b8') : 'var(--muted)';
      var prioLabel = alias('priority', m.priority) || (normPrio ? normPrio : '');
      var fullContent = m.content || "";
      var shortContent = fullContent.length > 60 ? fullContent.substring(0, 60) + "..." : fullContent;
      var titleAttr = fullContent.length > 60 ? ' title="' + escapeAttr(fullContent) + '"' : '';
      return '<div class="progress-row" onclick="setTab(\'actions\');setTimeout(function(){loadTaskBaseFromActions()},50)" style="cursor:pointer;">' +
        '<div class="progress-id">' + escapeHtml((m.group_title || m.id || "").replace(/^MEMO-\d{2}(\d{2})/, "$1")) + '</div>' +
        '<div class="progress-title"' + titleAttr + '>' + escapeHtml(shortContent) + '</div>' +
        (prioLabel ? '<span class="pill" style="background:' + prioBg + ';color:' + prioColor + ';font-size:11px;">' + escapeHtml(prioLabel) + '</span>' : '') +
        '</div>';
    }).join("");
    if (memos.length > 5) {
      itemsHtml += '<div class="progress-row" onclick="setTab(\'actions\');setTimeout(function(){loadTaskBaseFromActions()},50)" style="cursor:pointer;color:var(--muted);font-size:12px;">' +
        '<div class="progress-id"></div><div class="progress-title">还有 ' + (memos.length - 5) + ' 条备忘...</div><div class="progress-count"></div></div>';
    }
  }

  container.innerHTML = itemsHtml ? itemsHtml : '<p style="color:var(--muted);font-size:13px;">暂无</p>';
}

function renderFocusItem(item, isCritical) {
  var o = item.obj;
  var detail = o.block_reason || o.decision_needed || o.decision_point || o.human_gate || o.current_step || o.next_action || "";
  var icons = {blocked: "", waiting: "", review: "", executing: "", planned: ""};
  return '<div class="focus-item fi-' + item.type + '" onclick="loadTaskDetailFromOverview(\'' + escapeAttr(o.project || "") + '\',\'' + escapeAttr(o.doc_id || "") + '\',\'' + escapeAttr(o.id || "") + '\')">' +
    '<div class="focus-icon">' + (icons[item.type] || "") + '</div>' +
    '<div class="focus-body">' +
    '<div class="focus-title"><span class="focus-id">' + escapeHtml(o.id || "") + '</span> ' + escapeHtml(o.title || "") + '</div>' +
    (detail ? '<div class="focus-detail">' + escapeHtml(detail) + '</div>' : '') +
    '<div class="focus-pills"><span class="pill current">' + escapeHtml(alias('status', o.normalized_status || o.status)) + '</span>' +
    (o.priority ? '<span class="pill">' + escapeHtml(alias('priority', o.priority)) + '</span>' : '') + '</div>' +
    '</div></div>';
}

function loadTaskDetailFromOverview(project, docId, objId) {
  loadTaskDetail(project, docId, objId, "action");
}

function renderRequirementProgress() {
  var container = document.getElementById("progressList");
  if (!container) return;
  if (!_requirementOverviewData || !_requirementOverviewData.items || _requirementOverviewData.items.length === 0) {
    container.innerHTML = '<div style="color:var(--muted);padding:12px 0;font-size:13px;">需求全貌数据加载中，点击"需求"标签查看</div>';
    return;
  }
  var items = _requirementOverviewData.items;
  container.innerHTML = items.map(function(item, idx) {
    var d = item.derived || {};
    var tasks = item.tasks || [];
    var subs = item.sub_requirements || [];
    var total = tasks.length + subs.length;
    if (total === 0) total = 1;
    var closed = tasks.filter(function(t) { return (t.normalized_status || t.status) === "Closed" || (t.normalized_status || t.status) === "Cancelled"; }).length;
    subs.forEach(function(sub) {
      var st = sub.tasks || [];
      if (st.length > 0 && st.every(function(t) { return (t.normalized_status || t.status) === "Closed" || (t.normalized_status || t.status) === "Cancelled"; })) {
        closed++;
      }
    });
    var pct = Math.round((closed / total) * 100);
    var statusClass = "ps-executing";
    var barClass = "";
    if (d.status === "有阻塞" || d.status_class === "blocked") { statusClass = "ps-blocked"; barClass = "pf-blocked"; }
    else if (d.status === "待决策") { statusClass = "ps-waiting"; barClass = "pf-waiting"; }
    else if (d.status === "待验收") { statusClass = "ps-review"; barClass = "pf-review"; }
    else if (d.status === "已完成") { statusClass = "ps-done"; }
    else if (d.status === "已规划") { statusClass = "ps-planned"; }
    else if (d.status === "待规划") { statusClass = "ps-ready"; }
    var doc = item.requirement_doc || {};
    var html = '<div class="progress-row" onclick="setTab(\'requirements\');setTimeout(function(){renderRequirementOverviewDetail(' + idx + ')},100)" style="cursor:pointer;">' +
      '<div class="progress-id">' + escapeHtml(doc.id || item.project_name || "") + '</div>' +
      '<div class="progress-title">' + escapeHtml(doc.title || "") + '</div>' +
      '<div class="progress-bar-wrap"><div class="progress-bar-bg"><div class="progress-bar-fill ' + barClass + '" style="width:' + pct + '%;"></div></div></div>' +
      '<div class="progress-count">' + closed + '/' + total + '</div>' +
      '<div class="progress-status ' + statusClass + '">' + escapeHtml(alias('status', d.status) || d.status || "执行中") + '</div>' +
      '</div>';
    if (subs.length > 0) {
      subs.forEach(function(sub) {
        var sd = sub.derived || {};
        var st = sub.tasks || [];
        var stotal = st.length || 1;
        var sclosed = st.filter(function(t) { return (t.normalized_status || t.status) === "Closed" || (t.normalized_status || t.status) === "Cancelled"; }).length;
        var spct = Math.round((sclosed / stotal) * 100);
        var sstatusClass = "ps-executing";
        var sbarClass = "";
        if (sd.status === "有阻塞" || sd.status_class === "blocked") { sstatusClass = "ps-blocked"; sbarClass = "pf-blocked"; }
        else if (sd.status === "待决策") { sstatusClass = "ps-waiting"; sbarClass = "pf-waiting"; }
        else if (sd.status === "待验收") { sstatusClass = "ps-review"; sbarClass = "pf-review"; }
        else if (sd.status === "已完成") { sstatusClass = "ps-done"; }
        else if (sd.status === "已规划") { sstatusClass = "ps-planned"; }
        else if (sd.status === "待规划") { sstatusClass = "ps-ready"; }
        var sdoc = sub.requirement_doc || {};
        html += '<div class="progress-row sub-row" onclick="setTab(\'requirements\');setTimeout(function(){renderRequirementOverviewDetail(' + idx + ')},100)" style="cursor:pointer;">' +
          '<div class="progress-id">' + escapeHtml(sdoc.id || "") + '</div>' +
          '<div class="progress-title">' + escapeHtml(sdoc.title || "") + '</div>' +
          '<div class="progress-bar-wrap"><div class="progress-bar-bg"><div class="progress-bar-fill ' + sbarClass + '" style="width:' + spct + '%;"></div></div></div>' +
          '<div class="progress-count">' + sclosed + '/' + stotal + '</div>' +
          '<div class="progress-status ' + sstatusClass + '">' + escapeHtml(alias('status', sd.status) || sd.status || "执行中") + '</div>' +
          '</div>';
      });
    }
    return html;
  }).join("");
}

function renderRiskGates() {
  var container = document.getElementById("riskList");
  if (!container) return;
  var risks = [];
  if (_taskHealthData && _taskHealthData.items) {
    var humanGateCount = _taskHealthData.items.filter(function(i) { return i.human_gate; }).length;
    var missingClosureCount = _taskHealthData.items.filter(function(i) { return i.migration_priority === "P3"; }).length;
    if (humanGateCount > 0) risks.push({type: "warning", icon: "⚠️", label: "Human Gate 待确认", count: humanGateCount});
    if (missingClosureCount > 0) risks.push({type: "danger", icon: "⚠️", label: "关闭字段缺失", count: missingClosureCount});
  }
  if (pmOverview && pmOverview.summary) {
    var blocked = pmOverview.summary.blocked || 0;
    if (blocked > 0) risks.push({type: "danger", icon: "🔴", label: "阻塞任务", count: blocked});
  }
  if (risks.length === 0) {
    container.innerHTML = '<div class="risk-bar"><div class="risk-item"><span class="ri-icon">✅</span> 无风险信号</div></div>';
    return;
  }
  container.innerHTML = '<div class="risk-bar">' + risks.map(function(r) {
    return '<div class="risk-item ri-' + r.type + '"><span class="ri-icon">' + r.icon + '</span> ' + escapeHtml(r.label) + ' <span class="ri-count">' + r.count + '</span></div>';
  }).join("") + '</div>';
}

function renderRecentChanges() {
  var container = document.getElementById("recentList");
  if (!container) return;
  var changes = null;
  if (pmOverview && pmOverview.latest_changes && pmOverview.latest_changes.length > 0) {
    changes = pmOverview.latest_changes;
  } else if (state && state.latest_changes && state.latest_changes.length > 0) {
    changes = state.latest_changes;
  }
  if (!changes || changes.length === 0) {
    container.innerHTML = '<div style="color:var(--muted);padding:8px 0;font-size:13px;">暂无变化记录</div>';
    return;
  }
  var items = changes.slice(0, 10);
  var html = items.map(function(change, idx) {
    var changeId = "change-" + idx;
    var isExpanded = _expandedChangeId === changeId;
    var relativeTime = formatRelativeTime(change.date);
    var detailFile = change.detail_file || "";
    var project = change.project || "";
    var html = '<div class="recent-item ' + (isExpanded ? "recent-item-expanded" : "") + '" id="' + changeId + '">' +
      '<div class="recent-time" onclick="toggleChangeDetail(\'' + changeId + '\')" style="cursor:pointer;">' + escapeHtml(relativeTime) + '</div>' +
      '<div class="recent-body" onclick="toggleChangeDetail(\'' + changeId + '\')" style="cursor:pointer;">' +
        '<span class="recent-action">' + escapeHtml(change.title || change.summary || "") + '</span>' +
        '<span class="recent-expand-icon">' + (isExpanded ? "▾" : "▸") + '</span>' +
      '</div>';
    if (isExpanded && detailFile) {
      html += '<div class="recent-detail" id="' + changeId + '-detail">';
      html += '<div class="recent-detail-loading">加载中...</div>';
      html += '</div>';
    }
    html += '</div>';
    return html;
  }).join("");
  container.innerHTML = html;

  if (_expandedChangeId) {
    var detailEl = document.getElementById(_expandedChangeId + "-detail");
    var idx = parseInt(_expandedChangeId.replace("change-", ""), 10);
    var change = items[idx];
    if (detailEl && change && change.detail_file) {
      loadChangeDetail(detailEl, change.detail_file, change.project);
    }
  }
}

function toggleChangeDetail(changeId) {
  if (_expandedChangeId === changeId) {
    _expandedChangeId = null;
  } else {
    _expandedChangeId = changeId;
  }
  renderRecentChanges();
}

async function loadChangeDetail(container, detailFile, project) {
  if (!container || !detailFile) return;
  try {
    var docPath = "docs/logs/" + detailFile;
    var resp = await fetch("/api/doc?path=" + encodeURIComponent(docPath));
    if (!resp.ok) {
      container.innerHTML = '<div style="color:var(--muted);padding:8px 0;font-size:13px;">无法加载详情</div>';
      return;
    }
    var data = await resp.json();
    var content = data.content || "";
    container.innerHTML = parseLogContent(content);
  } catch(e) {
    container.innerHTML = '<div style="color:var(--muted);padding:8px 0;font-size:13px;">加载失败</div>';
  }
}

function parseLogContent(content) {
  if (!content) return "";
  var lines = content.split('\n');
  var items = [];
  var currentSection = '';
  var buffer = [];

  for (var i = 0; i < lines.length; i++) {
    var line = lines[i];
    var trimmed = line.trim();
    if (!trimmed) continue;

    if (trimmed.match(/^#{1,3}\s/)) {
      if (buffer.length > 0) {
        flushBuffer(items, currentSection, buffer);
        buffer = [];
      }
      currentSection = trimmed.replace(/^#{1,3}\s/, '').trim();
    } else if (trimmed.match(/^\d+\.\s/) || trimmed.match(/^[-*]\s/) || trimmed.match(/^[✅]/)) {
      buffer.push(trimmed);
    }
  }
  if (buffer.length > 0) flushBuffer(items, currentSection, buffer);

  if (items.length === 0) {
    return '<div class="log-raw-content">' + renderMarkdown(content) + '</div>';
  }

  var html = '';
  for (var j = 0; j < items.length; j++) {
    var item = items[j];
    var tagClass = getTagClass(item.section);
    html += '<div class="log-card">';
    html += '<span class="log-badge log-badge-' + tagClass + '">' + escapeHtml(item.section || '更新') + '</span>';
    if (item.details.length > 0) {
      for (var d = 0; d < item.details.length; d++) {
        html += '<div class="log-detail-line">' + formatDetailItem(item.details[d]) + '</div>';
      }
    }
    html += '</div>';
  }
  return html;
}

function flushBuffer(items, section, buffer) {
  if (buffer.length === 0) return;
  var details = [];
  for (var k = 0; k < buffer.length; k++) {
    var line = buffer[k].replace(/^[-*]\s+/, '').replace(/^\d+\.\s+/, '').replace(/\*\*/g, '');
    if (line) details.push(line);
  }
  items.push({section: section, details: details});
}

function getTagClass(section) {
  var map = {
    '修复问题': 'fix',
    '新增文档': 'doc',
    'UI 优化': 'ui',
    '任务推进': 'task',
    '验证状态': 'check',
    '问题修复': 'fix',
    '功能更新': 'feature',
    '变更': 'change',
    '影响范围': 'scope',
    '影响': 'impact',
    '验证': 'verify'
  };
  return map[section] || 'default';
}

function formatDetailItem(text) {
  if (text.startsWith('✅')) return '<span class="log-check">' + escapeHtml(text) + '</span>';
  if (text.startsWith('`') && text.endsWith('`')) return '<code>' + escapeHtml(text.slice(1, -1)) + '</code>';
  var parts = text.split(/`([^`]+)`/g);
  if (parts.length > 1) {
    var result = '';
    for (var i = 0; i < parts.length; i++) {
      if (i % 2 === 1) result += '<code>' + escapeHtml(parts[i]) + '</code>';
      else result += escapeHtml(parts[i]);
    }
    return result;
  }
  return escapeHtml(text);
}

function renderMarkdown(text) {
  if (!text) return "";
  var html = text;
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="lang-$1">$2</code></pre>');
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
  html = html.replace(/^### (.+)$/gm, '<div class="md-h3">$1</div>');
  html = html.replace(/^## (.+)$/gm, '<div class="md-h2">$1</div>');
  html = html.replace(/^# (.+)$/gm, '<div class="md-h1">$1</div>');
  html = html.replace(/^---$/gm, '<hr>');
  html = html.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  html = html.replace(/^\* (.+)$/gm, '<li>$1</li>');
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
  html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');
  html = html.replace(/<br>/g, '');
  html = html.replace(/\n\n/g, '</p><p>');
  html = html.replace(/\n/g, '<br>');
  return '<p>' + html + '</p>';
}

function formatRelativeTime(dateStr) {
  if (!dateStr) return "未知";

  var now = new Date();
  var then;

  var clean = dateStr.replace(/\s*[+-]\d{4}\s*$/, "");

  if (clean.indexOf("T") >= 0) {
    then = new Date(clean);
  } else if (clean.indexOf(" ") >= 0) {
    then = new Date(clean.replace(" ", "T"));
  } else {
    then = new Date(clean + "T00:00:00");
  }

  if (isNaN(then.getTime())) return dateStr;

  var diffMs = now - then;
  var diffSec = Math.floor(diffMs / 1000);
  var diffMin = Math.floor(diffSec / 60);
  var diffHour = Math.floor(diffMin / 60);
  var diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) return "刚刚";
  if (diffMin < 60) return diffMin + " 分钟前";
  if (diffHour < 24) return diffHour + " 小时前";
  if (diffDay < 7) return diffDay + " 天前";
  if (diffDay < 30) return Math.floor(diffDay / 7) + " 周前";
  if (diffDay < 365) return Math.floor(diffDay / 30) + " 月前";
  return Math.floor(diffDay / 365) + " 年前";
}

async function loadTaskHealth() {
  var summary = document.getElementById("taskHealthSummary");
  var list = document.getElementById("taskHealthList");
  if (!summary || !list) return;
  summary.innerHTML = '<div class="card"><p>加载中...</p></div>';
  try {
    var response = await fetch("/api/pm/task-health");
    if (!response.ok) throw new Error(await response.text());
    _taskHealthData = await response.json();
    var ss = _taskHealthData.status_summary || {};
    var totalWithIssues = 0;
    var statuses = ["Executing", "Decision Needed", "Blocked", "Review Needed", "Planned"];
    summary.innerHTML = statuses.map(function(st) {
      var count = ss[st] || 0;
      totalWithIssues += count;
      return '<div class="card"><h3>' + escapeHtml(alias('status', st)) + '</h3><div class="metric" style="color:' + (STATUS_COLORS[st] || '#94a3b8') + '">' + count + '</div></div>';
    }).join('');
    list.classList.remove("hidden");
    var items = (_taskHealthData.items || []).filter(function(it) { return it.health_issues && it.health_issues.length; });
    if (items.length === 0) {
      list.innerHTML = '<div class="card" style="grid-column:1/-1;"><p style="color:var(--muted);">所有对象健康度良好。</p></div>';
      return;
    }
    list.innerHTML = items.slice(0, 20).map(function(item) {
      var missing = (item.missing_fields || []).map(function(f) { return f.label; }).join("、");
      var issues = item.health_issues.map(function(i) { return escapeHtml(i); }).join("；");
      return '<div class="card">' +
        '<h3>' + escapeHtml(item.id) + ' · ' + escapeHtml(item.title) + ' <span class="pill" style="font-size:11px;">' + escapeHtml(alias('status', item.normalized_status)) + '</span></h3>' +
        '<p><span class="pill">' + escapeHtml(item.project_name) + '</span></p>' +
        (issues ? '<p style="color:var(--dim);font-size:12px;margin-top:6px;">问题：' + issues + '</p>' : '') +
        (missing ? '<p style="color:var(--dim);font-size:12px;margin-top:4px;">缺：' + escapeHtml(missing) + '</p>' : '') +
        (item.human_gate ? '<p style="color:#f97316;font-size:12px;">Human Gate</p>' : '') +
        '</div>';
    }).join("") + (items.length > 20 ? '<div class="card" style="grid-column:1/-1;"><p style="color:var(--muted);">...还有 ' + (items.length - 20) + ' 个对象</p></div>' : '');
  } catch (error) {
    summary.innerHTML = '<div class="error">' + escapeHtml(error.message) + '</div>';
  }
}

function render() {
  renderHealthBar();
  renderTaskMetricsPreview(pmOverview ? pmOverview.summary : null);
  renderMemoListOverview();
  renderRequirementProgress();
  renderRiskGates();
  renderRecentChanges();

  var actEl = document.getElementById("overviewActions");
  if (actEl && state.actions) {
    var pending = state.actions.filter(function(a) { return a.status !== "已完成"; });
    var actCountEl = document.getElementById("actCount");
    if (actCountEl) actCountEl.textContent = "(" + pending.length + ")";
    if (pending.length === 0) {
      actEl.innerHTML = '<div style="color:var(--muted);padding:8px;">暂无待办行动</div>';
    } else {
      var actHtml = '<table style="width:100%;border-collapse:collapse;font-size:13px;">';
      pending.slice(0, 10).forEach(function(a) {
        var normP = normalizePriority(a.priority);
        var prioBg = normP ? (PRIORITY_COLORS[normP] || '#94a3b8') + '22' : 'transparent';
        var prioColor = normP ? (PRIORITY_COLORS[normP] || '#94a3b8') : 'var(--muted)';
        var projName = PROJECTS[a.project] ? PROJECTS[a.project].name : a.project;
        actHtml += '<tr style="border-bottom:1px solid var(--border);">';
        actHtml += '<td style="padding:5px 8px;white-space:nowrap;width:50px;"><span class="pill" style="background:' + prioBg + ';color:' + prioColor + '">' + escapeHtml(normP || a.priority) + '</span></td>';
        actHtml += '<td style="padding:5px 8px;">' + escapeHtml(a.id ? a.id + " " + a.title : a.title) + '</td>';
        actHtml += '<td style="padding:5px 8px;color:var(--muted);white-space:nowrap;width:60px;text-align:right;">' + escapeHtml(projName) + '</td>';
        actHtml += '</tr>';
      });
      if (pending.length > 10) {
        actHtml += '<tr><td colspan="3" style="padding:5px 8px;color:var(--muted);font-style:italic;">...还有 ' + (pending.length - 10) + ' 条</td></tr>';
      }
      actHtml += '</table>';
      actEl.innerHTML = actHtml;
    }
  }

  loadAuditLog();
}

function buildProjectSelector(containerId, activeProject, onSelectFn) {
  var container = document.getElementById(containerId);
  var html = '<button class="proj-btn ' + (!activeProject ? "active" : "") + '" data-proj="">全部</button>';
  Object.keys(PROJECTS).forEach(function(key) {
    var p = PROJECTS[key];
    html += '<button class="proj-btn ' + (activeProject === key ? "active" : "") + '" data-proj="' + key + '">' + escapeHtml(p.name) + "</button>";
  });
  container.innerHTML = html;
  container.querySelectorAll(".proj-btn").forEach(function(btn) {
    btn.addEventListener("click", function() {
      onSelectFn(btn.dataset.proj);
    });
  });
}

function debounceReqSearch() {
  clearTimeout(_reqSearchTimer);
  _reqSearchTimer = setTimeout(loadRequirements, 300);
}

function debounceMemoSearch() {
  clearTimeout(_memoSearchTimer);
  _memoSearchTimer = setTimeout(loadTaskBase, 300);
}

function selectReqProject(project) {
  _reqProjectFilter = project;
  buildProjectSelector("reqProjectSelector", _reqProjectFilter, selectReqProject);
  loadRequirements();
}

function selectMemoProject(project) {
  _memoProjectFilter = project;
  buildProjectSelector("memoProjectSelector", _memoProjectFilter, selectMemoProject);
  renderTaskBase();
}

function setReqView(mode) {
  _reqViewMode = mode;
  document.getElementById("reqViewList").classList.toggle("active", mode === "list");
  document.getElementById("reqViewKanban").classList.toggle("active", mode === "kanban");
  document.getElementById("reqList").classList.toggle("hidden", mode === "kanban");
  document.getElementById("reqKanban").classList.toggle("hidden", mode === "list");
  if (mode === "kanban") loadActionBoard();
  else if (_reqData) renderReqList(_reqData);
}

function setMemoView(mode) {
  _memoViewMode = mode;
  document.getElementById("memoViewList").classList.toggle("active", mode === "list");
  document.getElementById("memoViewKanban").classList.toggle("active", mode === "kanban");
  document.getElementById("memoList").classList.toggle("hidden", mode === "kanban");
  document.getElementById("memoKanban").classList.toggle("hidden", mode === "list");
  if (_memoData) {
    if (mode === "kanban") renderMemoKanban(_memoData);
    else renderMemoList(_memoData);
  }
}

async function loadTaskBase() {
  var summary = document.getElementById("taskBaseSummary");
  if (summary) summary.innerHTML = '<div class="card"><p>加载中...</p></div>';
  try {
    var response = await fetch("/api/pm/task-base");
    if (!response.ok) throw new Error(await response.text());
    _taskBaseData = await response.json();
    renderTaskBase();
  } catch (error) {
    if (summary) summary.innerHTML = '<div class="error">' + escapeHtml(error.message) + '</div>';
  }
}

function selectedTaskBaseProjects() {
  if (!_taskBaseData) return [];
  return (_taskBaseData.projects || []).filter(function(project) {
    return !_memoProjectFilter || project.project === _memoProjectFilter;
  });
}

function renderTaskBase() {
  if (!_taskBaseData) return;
  buildProjectSelector("memoProjectSelector", _memoProjectFilter, selectMemoProject);
  var projects = selectedTaskBaseProjects();
  var summary = {tasks: 0, memos: 0, open_memos: 0, closed_memos: 0};
  projects.forEach(function(project) {
    Object.keys(summary).forEach(function(key) { summary[key] += (project.summary && project.summary[key]) || 0; });
  });
  var summaryEl = document.getElementById("taskBaseSummary");
  if (summaryEl) {
    summaryEl.innerHTML =
      '<div class="card"><h3>任务对象</h3><div class="metric" style="color:var(--cyan)">' + summary.tasks + '</div></div>' +
      '<div class="card"><h3>未处理备忘</h3><div class="metric" style="color:var(--yellow)">' + summary.open_memos + '</div></div>' +
      '<div class="card"><h3>已关闭备忘</h3><div class="metric" style="color:var(--green)">' + summary.closed_memos + '</div></div>';
  }
  var tasks = [];
  var memos = [];
  projects.forEach(function(project) {
    tasks = tasks.concat(project.tasks || []);
    memos = memos.concat(project.memos || []);
  });
  _memoData = memos;
  renderTaskBaseTasks(tasks);
  if (_memoViewMode === "kanban") renderMemoKanban(memos);
  else renderMemoList(memos);
}

function renderTaskBaseTasks(tasks) {
  var container = document.getElementById("taskBaseTasks");
  if (!container) return;
  if (!tasks.length) {
    container.innerHTML = '<p style="color:var(--muted);">暂无 Task。</p>';
    return;
  }
  container.innerHTML = tasks.map(function(task) {
    return '<div style="padding:10px 0;border-bottom:1px solid rgba(51,65,85,0.45);">' +
      '<strong style="color:var(--cyan);">' + escapeHtml(task.id || "") + '</strong> ' + escapeHtml(task.title || "") +
      '<p><span class="pill current">' + escapeHtml(alias('status', task.normalized_status || task.status)) + '</span><span class="pill">' + escapeHtml(alias('priority', task.priority) || "-") + '</span><span class="pill">' + escapeHtml(task.requirement_doc || "未关联") + '</span></p>' +
      '<p style="color:var(--dim);font-size:12px;">' + escapeHtml(task.path || "") + '</p>' +
      '</div>';
  }).join("");
}

async function loadRequirements() {
  var summary = document.getElementById("reqSummary");
  var list = document.getElementById("reqList");
  summary.innerHTML = '<div class="card"><p>加载中...</p></div>';
  list.innerHTML = "";
  try {
    var params = new URLSearchParams();
    var search = document.getElementById("reqSearch").value;
    var filterStatus = document.getElementById("reqFilterStatus").value;
    var filterPriority = document.getElementById("reqFilterPriority").value;
    if (search) params.set("search", search);
    if (filterStatus) params.set("obj_status", filterStatus);
    if (filterPriority) params.set("priority", filterPriority);
    if (_reqProjectFilter) params.set("project", _reqProjectFilter);
    var response = await fetch("/api/requirements?" + params.toString());
    if (!response.ok) throw new Error(await response.text());
    var data = await response.json();
    _reqData = data.requirements || [];
    renderReqSummary(_reqData);
    renderReqList(_reqData);
    if (_reqViewMode === "kanban") await loadActionBoard();
  } catch (error) {
    summary.innerHTML = '<div class="error">' + escapeHtml(error.message) + "</div>";
  }
}

async function loadRequirementOverview() {
  var summary = document.getElementById("requirementOverviewSummary");
  var list = document.getElementById("requirementOverviewList");
  var detail = document.getElementById("requirementOverviewDetail");
  if (summary) summary.innerHTML = '<div class="card"><p>加载中...</p></div>';
  if (list) list.innerHTML = "";
  try {
    var response = await fetch("/api/pm/requirement-overview");
    if (!response.ok) throw new Error(await response.text());
    _requirementOverviewData = await response.json();
    renderRequirementOverview(_requirementOverviewData);
    if (detail && !detail.dataset.selected) {
      detail.innerHTML = '<p style="color:var(--muted);">选择左侧需求查看详情和 AI 上下文。</p>';
    }
  } catch (error) {
    if (summary) summary.innerHTML = '<div class="error">' + escapeHtml(error.message) + '</div>';
  }
}

function renderRequirementOverview(data) {
  var summary = document.getElementById("requirementOverviewSummary");
  var list = document.getElementById("requirementOverviewList");
  var scope = document.getElementById("requirementOverviewScope");
  if (!summary || !list) return;
  var s = data.summary || {};
  if (scope) scope.textContent = data.scope || "";
  summary.innerHTML =
    '<div class="card"><h3>需求数</h3><div class="metric">' + (s.requirements || 0) + '</div></div>' +
    '<div class="card"><h3>开放任务</h3><div class="metric" style="color:var(--cyan)">' + (s.open_tasks || 0) + '</div></div>' +
    '<div class="card"><h3>阻塞 <span style="font-size:11px;color:var(--dim);font-weight:normal;">卡住无法继续</span></h3><div class="metric" style="color:var(--red)">' + (s.blocked_tasks || 0) + '</div></div>' +
    '<div class="card"><h3>待决策 <span style="font-size:11px;color:var(--dim);font-weight:normal;">需人类判断</span></h3><div class="metric" style="color:var(--orange)">' + (s.decision_needed_tasks || 0) + '</div></div>' +
    '<div class="card"><h3>待验收 <span style="font-size:11px;color:var(--dim);font-weight:normal;">做完了等确认</span></h3><div class="metric" style="color:var(--blue)">' + (s.review_needed_tasks || 0) + '</div></div>' +
    '<div class="card"><h3>未处理备忘</h3><div class="metric" style="color:var(--yellow)">' + (s.open_memos || 0) + '</div></div>';
  var items = data.items || [];
  if (!items.length) {
    list.innerHTML = '<div class="card"><p style="color:var(--muted);">暂无需求文档。</p></div>';
    return;
  }
  list.innerHTML = items.map(function(item, idx) {
    var doc = item.requirement_doc || {};
    var d = item.derived || {};
    var cls = d.status_class || "";
    var subs = item.sub_requirements || [];
    var subHtml = "";
    if (subs.length > 0) {
      subHtml = '<div style="margin-top:10px;padding-left:12px;border-left:2px solid var(--border);">' +
        '<div style="font-size:11px;color:var(--dim);margin-bottom:6px;">子需求 ' + subs.length + '</div>' +
        subs.map(function(sub, si) {
          var sd = sub.derived || {};
          var sdoc = sub.requirement_doc || {};
          var sclazz = sd.status_class || "";
          return '<div style="padding:6px 0;border-bottom:1px solid rgba(51,65,85,0.3);cursor:pointer;display:flex;justify-content:space-between;align-items:center;" onclick="event.stopPropagation();renderRequirementOverviewDetail(' + idx + ',' + si + ')">' +
            '<div><span style="color:var(--cyan);font-family:Fira Code,monospace;font-size:12px;">' + escapeHtml(sdoc.id || "") + '</span> ' +
            escapeHtml(sdoc.title || "") + ' ' +
            '<span class="pill ' + escapeAttr(sclazz) + '">' + escapeHtml(alias('status', sd.status)) + '</span> ' +
            '<span style="color:var(--dim);font-size:11px;">任务 ' + (sub.tasks || []).length + '</span></div>' +
            '<span style="color:var(--dim);font-size:14px;">›</span></div>';
        }).join("") +
        '</div>';
    }
    return '<div class="card" onclick="renderRequirementOverviewDetail(' + idx + ')" style="cursor:pointer;">' +
      '<h3>' + escapeHtml(doc.id || "") + ' · ' + escapeHtml(doc.title || "") + ' <span class="pill ' + escapeAttr(cls) + '">' + escapeHtml(alias('status', d.status)) + '</span></h3>' +
      '<p style="color:var(--dim);">' + escapeHtml(item.project_name || "") + ' · ' + escapeHtml(doc.path || "") + '</p>' +
      '<p style="margin-top:8px;"><span class="pill">优先级: ' + escapeHtml(normalizePriority(d.highest_priority) || d.highest_priority || "-") + '</span></p>' +
      '<p style="margin-top:8px;color:var(--muted);font-size:13px;">任务 ' + (item.tasks || []).length + ' · 开放 ' + (d.open_task_count || 0) + ' · <span style="color:var(--red);">🔴阻塞 ' + (d.blocked_task_count || 0) + '</span> · <span style="color:var(--orange);">🟡待决策 ' + (d.decision_needed_count || 0) + '</span> · <span style="color:#3b82f6;">🔵待验收 ' + (d.review_needed_count || 0) + '</span> · 备忘 ' + (d.open_memo_count || 0) + '</p>' +
      subHtml +
      '<div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;"><button class="btn sm" onclick="event.stopPropagation();openSourceDoc(\'' + escapeHtml(doc.path || "") + '\')">源文档</button><button class="btn sm primary" onclick="event.stopPropagation();copyRequirementContext(' + idx + ', this)">复制 AI 上下文</button></div>' +
      '</div>';
  }).join("");
  renderRequirementOverviewDetail(0);
}

function renderRequirementOverviewDetail(index, subIndex) {
  if (!_requirementOverviewData) return;
  var parentItem = (_requirementOverviewData.items || [])[index];
  var detail = document.getElementById("requirementOverviewDetail");
  if (!parentItem || !detail) return;
  var item = parentItem;
  var breadcrumb = '';
  if (typeof subIndex === 'number' && subIndex >= 0) {
    var subs = parentItem.sub_requirements || [];
    if (subs[subIndex]) {
      item = subs[subIndex];
      var pdoc = parentItem.requirement_doc || {};
      breadcrumb = '<div style="margin-bottom:10px;display:flex;align-items:center;gap:6px;font-size:13px;">' +
        '<a href="javascript:void(0)" onclick="renderRequirementOverviewDetail(' + index + ')" style="color:var(--cyan);text-decoration:none;">' + escapeHtml(pdoc.id || "") + ' ' + escapeHtml(pdoc.title || "") + '</a>' +
        '<span style="color:var(--dim);">›</span>' +
        '<span style="color:var(--text);">' + escapeHtml((item.requirement_doc || {}).id || "") + '</span>' +
        '</div>';
    }
  }
  detail.dataset.selected = String(index);
  var doc = item.requirement_doc || {};
  var d = item.derived || {};
  var tasks = item.tasks || [];
  var memos = item.memos || [];
  var reading = item.recommended_reading || [];
  var subs = item.sub_requirements || [];
  var subDetailHtml = "";
  if (subs.length > 0) {
    subDetailHtml = '<div class="task-detail-section" style="margin-top:14px;"><h4>子需求</h4>' +
      subs.map(function(sub, si) {
        var sd = sub.derived || {};
        var sdoc = sub.requirement_doc || {};
        var stasks = sub.tasks || [];
        var sclazz = sd.status_class || "";
        return '<div style="padding:10px 0;border-bottom:1px solid rgba(51,65,85,0.45);cursor:pointer;" onclick="renderRequirementOverviewDetail(' + index + ',' + si + ')">' +
          '<div style="display:flex;justify-content:space-between;align-items:center;">' +
          '<div><strong style="color:var(--cyan);">' + escapeHtml(sdoc.id || "") + '</strong> ' + escapeHtml(sdoc.title || "") +
          ' <span class="pill ' + escapeAttr(sclazz) + '">' + escapeHtml(alias('status', sd.status)) + '</span></div>' +
          '<span style="color:var(--dim);font-size:18px;">›</span></div>' +
          '<p style="color:var(--dim);font-size:12px;margin-top:4px;">任务 ' + stasks.length + ' · 开放 ' + (sd.open_task_count || 0) + ' · 阻塞 ' + (sd.blocked_task_count || 0) + '</p>' +
          '</div>';
      }).join("") +
      '</div>';
  }
  detail.innerHTML = breadcrumb +
    '<div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;">' +
    '<div><h3 style="margin:0;">' + escapeHtml(doc.id || "") + ' · ' + escapeHtml(doc.title || "") + '</h3>' +
    '<p style="color:var(--muted);margin-top:6px;">' + escapeHtml(item.project_name || "") + ' / ' + escapeHtml(doc.path || "") + '</p></div>' +
    '<div style="display:flex;gap:8px;flex-wrap:wrap;"><button class="btn sm" onclick="openSourceDoc(\'' + escapeHtml(doc.path || "") + '\')">源文档</button><button class="btn sm primary" onclick="copyRequirementContext(' + index + ', this)">复制 AI 上下文</button></div>' +
    '</div>' +
    '<div class="grid cols-4" style="margin-top:14px;">' +
    '<div class="card"><h3>状态</h3><p><span class="pill ' + escapeAttr(d.status_class || "") + '">' + escapeHtml(alias('status', d.status)) + '</span></p></div>' +
    '<div class="card"><h3>开放任务</h3><div class="metric" style="font-size:24px;color:var(--cyan)">' + (d.open_task_count || 0) + '</div></div>' +
    '<div class="card"><h3>阻塞 <span style="font-size:10px;color:var(--dim);font-weight:normal;">卡住无法继续</span></h3><div class="metric" style="font-size:24px;color:var(--red)">' + (d.blocked_task_count || 0) + '</div></div>' +
    '<div class="card"><h3>待决策 <span style="font-size:10px;color:var(--dim);font-weight:normal;">需人类判断</span></h3><div class="metric" style="font-size:24px;color:var(--orange)">' + (d.decision_needed_count || 0) + '</div></div>' +
    '</div>' +
    '<div class="grid cols-4" style="margin-top:8px;">' +
    '<div class="card"><h3>待验收 <span style="font-size:10px;color:var(--dim);font-weight:normal;">做完了等确认</span></h3><div class="metric" style="font-size:24px;color:#3b82f6">' + (d.review_needed_count || 0) + '</div></div>' +
    '<div class="card"><h3>未处理备忘</h3><div class="metric" style="font-size:24px;color:var(--yellow)">' + (d.open_memo_count || 0) + '</div></div>' +
    '</div>' +
    '<div class="task-detail-grid">' +
    '<div class="task-detail-section"><h4>需求摘要</h4>' +
    '<div class="task-detail-row"><div class="task-detail-label">关联文档</div><div class="task-detail-value">' + escapeHtml(emptyValue(doc.path)) + '</div></div>' +
    '<div class="task-detail-row"><div class="task-detail-label">目标</div><div class="task-detail-value">' + escapeHtml(emptyValue(doc.goal)) + '</div></div>' +
    '<div class="task-detail-row"><div class="task-detail-label">范围</div><div class="task-detail-value">' + escapeHtml(emptyValue(doc.scope)) + '</div></div>' +
    '</div>' +
    '<div class="task-detail-section"><h4>推荐阅读</h4>' + (reading.length ? reading.map(function(path) { return '<p><button class="btn sm" onclick="openSourceDoc(\'' + escapeHtml(path) + '\')">' + escapeHtml(path) + '</button></p>'; }).join("") : '<p style="color:var(--muted);">暂无推荐阅读</p>') + '</div>' +
    '</div>' +
    '<div class="task-detail-section" style="margin-top:14px;"><h4>关联任务</h4>' +
    (tasks.length ? tasks.map(function(task) { return '<div style="padding:10px 0;border-bottom:1px solid rgba(51,65,85,0.45);cursor:pointer;" onclick="event.stopPropagation();navigateToTask(\'' + escapeAttr(task.project_id || item.project_id || "") + '\',\'' + escapeAttr(task.doc_id || "") + '\',\'' + escapeAttr(task.id || "") + '\')"><strong style="color:var(--cyan);">' + escapeHtml(task.id || "") + '</strong> ' + escapeHtml(task.title || "") + '<p><span class="pill current">' + escapeHtml(alias('status', task.normalized_status || task.status)) + '</span><span class="pill">' + escapeHtml(alias('priority', task.priority) || "-") + '</span></p><p style="color:var(--dim);font-size:12px;">' + escapeHtml(task.path || "") + '</p></div>'; }).join("") : '<p style="color:var(--muted);">暂无关联任务</p>') +
    '</div>' +
    '<div class="task-detail-section" style="margin-top:14px;"><h4>未处理 Memo</h4>' +
    (memos.length ? memos.map(function(memo) { return '<div style="padding:10px 0;border-bottom:1px solid rgba(51,65,85,0.45);cursor:pointer;" onclick="event.stopPropagation();openSourceDoc(\'' + escapeHtml(memo.path || "") + '\')"><strong style="color:var(--yellow);">' + escapeHtml(memo.id || "") + '</strong> ' + escapeHtml(memo.title || memo.content || "") + '<p style="color:var(--dim);font-size:12px;">' + escapeHtml(memo.path || "") + '</p></div>'; }).join("") : '<p style="color:var(--muted);">暂无关联未处理备忘</p>') +
    '</div>' +
    subDetailHtml +
    '<div class="task-detail-section" style="margin-top:14px;"><h4>AI 上下文预览</h4><textarea readonly style="width:100%;min-height:220px;border:1px solid var(--border);border-radius:var(--radius-md);background:rgba(15,23,42,0.75);color:var(--text);padding:12px;font-family:Fira Code,monospace;font-size:12px;">' + escapeHtml(item.ai_context || "") + '</textarea></div>';
}

function copyRequirementContext(index, btn) {
  if (!_requirementOverviewData) return;
  var item = (_requirementOverviewData.items || [])[index];
  if (!item) return;
  function onSuccess() {
    var orig = btn.textContent;
    btn.textContent = "已复制";
    setTimeout(function() { btn.textContent = orig; }, 1500);
  }
  var text = item.ai_context || "";
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(onSuccess).catch(function() { fallbackCopy(text, btn, onSuccess); });
  } else {
    fallbackCopy(text, btn, onSuccess);
  }
}

function renderReqSummary(reqs) {
  var allObjs = [];
  reqs.forEach(function(r) { allObjs = allObjs.concat(r.exec_objects || []); });
  var objByStatus = {};
  allObjs.forEach(function(o) { objByStatus[o.status] = (objByStatus[o.status] || 0) + 1; });
  var totalDeps = reqs.reduce(function(sum, r) { return sum + (r.dependencies ? r.dependencies.length : 0); }, 0);
  document.getElementById("reqSummary").innerHTML =
    '<div class="card"><h3>行动文档</h3><div class="metric">' + reqs.length + '</div></div>' +
    '<div class="card"><h3>执行对象</h3><div class="metric" style="color:var(--cyan)">' + allObjs.length + '</div></div>' +
    '<div class="card"><h3>待办对象</h3><div class="metric" style="color:var(--yellow)">' + (objByStatus["待办"] || 0) + '</div></div>' +
    '<div class="card"><h3>依赖项</h3><div class="metric" style="color:var(--orange)">' + totalDeps + "</div></div>";
}

function renderReqList(reqs) {
  var list = document.getElementById("reqList");
  if (reqs.length === 0) {
    list.innerHTML = '<div class="card" style="grid-column:1/-1;"><p style="color:var(--muted);">暂无匹配的需求文档。</p></div>';
    return;
  }
  list.innerHTML = reqs.map(function(req) {
    var statusClass = req.status === "进行中" ? "current" : req.status === "已完成" ? "done" : req.status === "待办" ? "next" : "";
    var objs = (req.exec_objects && req.exec_objects.length) ? req.exec_objects.map(function(obj) {
      var objStatusClass = obj.status === "待办" ? "next" : obj.status === "进行中" ? "current" : obj.status === "已完成" ? "done" : "";
      var blocked = obj.blocked_by && obj.blocked_by.length;
      return '<div style="margin-top:8px;padding:8px;border:1px solid var(--border);border-radius:8px;background:rgba(15,23,42,.55);' + (blocked ? "border-top:2px solid #ef4444;" : "") + '">' +
        '<strong style="color:var(--cyan);">' + escapeHtml(obj.id) + "</strong> " + escapeHtml(obj.title) +
        ' <span class="pill ' + objStatusClass + '" style="margin-left:6px;">' + escapeHtml(alias('status', obj.status)) + "</span>" +
        ' <span class="pill" style="margin-left:4px;">' + escapeHtml(obj.type) + "</span>" +
        (obj.priority ? ' <span class="pill" style="margin-left:4px;">' + escapeHtml(alias('priority', obj.priority)) + "</span>" : "") +
        (blocked ? ' <span class="pill" style="margin-left:4px;background:#ef444422;color:#ef4444;">\u{1F6AB}</span>' : "") +
        (blocked ? '<div style="color:#ef4444;font-size:11px;margin-top:4px;">等待：' + obj.blocked_by.map(function(b) { return escapeHtml(b); }).join(" → ") + "</div>" : "") +
        (obj.prerequisite && !blocked ? '<div style="color:var(--dim);font-size:11px;margin-top:2px;">前置：' + escapeHtml(obj.prerequisite) + "</div>" : "") +
        "</div>";
    }).join("") : '<p style="color:var(--dim);margin-top:8px;">暂无执行对象</p>';
    var deps = (req.dependencies && req.dependencies.length) ? req.dependencies.slice(0, 3).map(function(d) {
      return '<span class="pill" style="margin-right:4px;">' + escapeHtml(d.type) + "</span>" +
        '<span style="color:var(--dim);font-size:12px;">' + escapeHtml(d.target) + "</span>";
    }).join("<br>") + (req.dependencies.length > 3 ? '<br><span style="color:var(--dim);font-size:11px;">...还有 ' + (req.dependencies.length - 3) + " 项</span>" : "") : "";
    return '<div class="card">' +
      "<h3>" + escapeHtml(req.id) + " · " + escapeHtml(req.title) + ' <span class="pill ' + statusClass + '">' + escapeHtml(req.status) + "</span></h3>" +
      '<p style="color:var(--dim);">' + escapeHtml(req.path) + "</p>" +
      objs +
      (deps ? '<div style="margin-top:10px;padding-top:8px;border-top:1px solid var(--border);"><p style="color:var(--muted);font-size:12px;margin-bottom:4px;">依赖关系</p>' + deps + "</div>" : "") +
      '<div style="margin-top:10px;"><button class="btn" onclick="loadDoc(\'' + escapeHtml(req.path) + "');setTab('docs');\">查看全文</button></div></div>";
  }).join("");
}

function renderReqKanban(reqs) {
  loadActionBoard();
}

async function loadActionBoard() {
  var container = document.getElementById("reqKanban");
  if (!container) return;
  container.innerHTML = '<div class="card"><p>加载中...</p></div>';
  try {
    var response = await fetch("/api/pm/action-board");
    if (!response.ok) throw new Error(await response.text());
    _actionBoardData = await response.json();
    renderActionBoard(_actionBoardData);
  } catch (error) {
    container.innerHTML = '<div class="error">' + escapeHtml(error.message) + '</div>';
  }
}

function actionBoardFilteredColumns(data) {
  var search = (document.getElementById("reqSearch").value || "").toLowerCase();
  var filterStatus = document.getElementById("reqFilterStatus").value;
  var filterPriority = document.getElementById("reqFilterPriority").value;
  var statusCompat = {"待办": "Planned", "进行中": "Executing", "阻塞": "Blocked", "待验证": "Review Needed", "已完成": "Closed", "已取消": "Cancelled", "待确认": "Decision Needed"};
  var normalizedFilter = statusCompat[filterStatus] || filterStatus;
  return (data.columns || []).map(function(col) {
    var items = (col.items || []).filter(function(item) {
      var matchesSearch = !search || [item.id, item.title, item.doc_title, item.project_name].join(" ").toLowerCase().indexOf(search) >= 0;
      var matchesStatus = !filterStatus || item.normalized_status === normalizedFilter || item.status === filterStatus;
      var matchesPriority = !filterPriority || item.priority === filterPriority;
      var matchesProject = !_reqProjectFilter || item.project === _reqProjectFilter;
      return matchesSearch && matchesStatus && matchesPriority && matchesProject;
    });
    return {key: col.key, items: items};
  });
}

function renderActionBoard(data) {
  var container = document.getElementById("reqKanban");
  var columns = actionBoardFilteredColumns(data || {columns: []});
  var colors = STATUS_COLORS;
  var wipLimits = {"Ready for Plan": 5, "Planned": 10, "Executing": 15, "Blocked": 5, "Decision Needed": 5, "Review Needed": 10, "Closed": 999, "Cancelled": 999, "Unknown": 999};
  container.innerHTML = '<div class="kanban" style="grid-template-columns:repeat(5,minmax(220px,1fr));overflow-x:auto;">' + columns.map(function(col) {
    var safeKey = escapeAttr(col.key);
    var itemCount = col.items.length;
    var wipLimit = wipLimits[col.key] || 999;
    var wipLabel = '<span class="kanban-col-wip">WIP ' + itemCount + '/' + wipLimit + (itemCount > wipLimit ? ' ⚠️' : '') + '</span>';
    return '<div class="kanban-col" data-status="' + safeKey + '" ondragover="onDragOver(event)" ondrop="onReqDrop(event, \'' + safeKey + '\')" ondragleave="onDragLeave(event)">' +
      '<div class="kanban-col-header"><div class="kanban-col-dot" style="background:' + (colors[col.key] || '#94a3b8') + ';"></div><span class="kanban-col-title">' + escapeHtml(alias('status', col.key)) + '</span><span class="kanban-col-count">' + itemCount + '</span>' + wipLabel + '</div>' +
      '<div class="kanban-cards">' +
      (col.items.length === 0 ? '<p style="color:var(--dim);text-align:center;padding:24px 0;">空</p>' : col.items.map(renderActionBoardCard).join("")) +
      '</div></div>';
  }).join("") + '</div>';
}

function renderActionBoardCard(item) {
  var projName = PROJECTS[item.project] ? PROJECTS[item.project].name : emptyValue(item.project_name || item.project);
  var focus = item.block_reason || item.decision_needed || item.human_gate || item.current_step || item.next_action || "";
  var blocked = item.blocked_by && item.blocked_by.length;
  var allowed = item.allowed_next_statuses || [];
  var normPrio = normalizePriority(item.priority);
  return '<div class="kanban-card' + (blocked || item.block_reason ? ' blocked' : '') + '" draggable="true" ondragstart="onReqDragStart(event)" data-obj-id="' + escapeAttr(item.id || "") + '" data-project="' + escapeAttr(item.project || "") + '" data-doc-id="' + escapeAttr(item.doc_id || "") + '" data-status="' + escapeAttr(item.normalized_status || item.status || "") + '" data-allowed="' + escapeAttr(allowed.join(",")) + '">' +
    '<div class="kanban-card-badges">' +
    '<span style="color:var(--cyan);font-weight:600;font-size:12px;">' + escapeHtml(emptyValue(item.id)) + '</span>' +
    (normPrio ? '<span class="priority-badge p' + normPrio.charAt(1) + '">' + escapeHtml(normPrio) + '</span>' : '') +
    '<span class="pill current">' + escapeHtml(alias('status', item.normalized_status || item.status)) + '</span>' +
    '<span class="pill">' + escapeHtml(emptyValue(item.type)) + '</span>' +
    '</div>' +
    '<p class="kanban-card-title">' + escapeHtml(emptyValue(item.title)) + '</p>' +
    '<p class="kanban-card-meta">来源：' + escapeHtml(projName) + ' / ' + escapeHtml(emptyValue(item.doc_id)) + ' · ' + escapeHtml(emptyValue(item.doc_title)) + '</p>' +
    (blocked ? '<div class="blocked-indicator">🔴 等待：' + item.blocked_by.map(function(b) { return escapeHtml(b); }).join(" → ") + '</div>' : '') +
    (focus && !blocked ? '<p style="font-size:12px;color:var(--muted);margin:6px 0 0;white-space:pre-wrap;">' + escapeHtml(emptyValue(focus)) + '</p>' : '') +
    (allowed.length ? '<p style="font-size:11px;color:var(--dim);margin:4px 0 0;">可流转：' + allowed.map(function(s) { return escapeHtml(alias('status', s)); }).join(' / ') + '</p>' : '<p style="font-size:11px;color:var(--dim);margin:4px 0 0;">无可流转状态</p>') +
    '<div class="kanban-card-actions"><button class="btn sm primary" onclick="loadTaskDetail(\'' + escapeHtml(item.project || "") + '\',\'' + escapeHtml(item.doc_id || "") + '\',\'' + escapeHtml(item.id || "") + '\',\'action\')">详情</button><button class="btn sm" onclick="openSourceDoc(\'' + escapeHtml(item.path || "") + '\')">源文档</button></div>' +
    '</div>';
}

async function loadTaskDetail(project, docId, objId, context) {
  var overlay = document.getElementById("taskDetailOverlay");
  if (!overlay) return;
  overlay.classList.add("open");
  document.getElementById("taskDetailPanel").classList.add("open");
  document.getElementById("taskDetailTitle").textContent = "加载任务详情...";
  document.getElementById("taskDetailBody").innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">加载中...</p>';
  try {
    var response = await fetch("/api/pm/tasks/" + encodeURIComponent(project) + "/" + encodeURIComponent(docId) + "/" + encodeURIComponent(objId));
    if (!response.ok) throw new Error(await response.text());
    var data = await response.json();
    renderTaskDetailPanel(data);
  } catch (error) {
    document.getElementById("taskDetailBody").innerHTML = '<div class="error">' + escapeHtml(error.message) + '</div>';
  }
}

function renderTaskDetailPanel(data) {
  var source = data.source || {};
  document.getElementById("taskDetailTitle").textContent = (data.id || "") + " " + (data.title || "");

  var statusStr = alias('status', data.normalized_status || data.status);
  var priorityStr = alias('priority', data.priority);
  var requirementDoc = data.requirement_doc || source.doc_title || "-";

  var sections = data.sections || [];
  var sectionsHtml = '';
  sections.forEach(function(section) {
    var fieldsHtml = (section.fields || []).map(function(field) {
      return '<div class="task-detail-row"><div class="task-detail-label">' + escapeHtml(field.label) + '</div><div class="task-detail-value">' + escapeHtml(emptyValue(field.value)) + '</div></div>';
    }).join("");
    sectionsHtml += '<div class="task-detail-section"><h4>' + escapeHtml(section.title) + '</h4>' + fieldsHtml + '</div>';
  });

  var allowed = data.allowed_next_statuses || [];
  var buttonsHtml = '';
  allowed.forEach(function(s) {
    var sLabel = alias('status', s);
    buttonsHtml += '<button class="btn sm primary" onclick="transitionTaskFromPanel(\'' + escapeHtml(s) + '\')">' + escapeHtml(sLabel) + '</button>';
  });
  document.getElementById("taskDetailBody").innerHTML =
    '<div class="panel-basic-info">' +
    '<div class="panel-status-row">' +
    '<span class="pill current">' + escapeHtml(statusStr) + '</span>' +
    (data.priority ? '<span class="pill">' + escapeHtml(priorityStr) + '</span>' : '') +
    '<span class="pill">' + escapeHtml(requirementDoc) + '</span>' +
    '</div>' +
    '</div>' +
    sectionsHtml +
    '<div class="panel-ai-section" style="margin-top:14px;">' +
    '<h4>🤖 AI 上下文</h4>' +
    (data.ai_context ? '<textarea readonly style="width:100%;min-height:120px;border:1px solid var(--border);border-radius:var(--radius-md);background:rgba(15,23,42,0.75);color:var(--text);padding:10px;font-family:Fira Code,monospace;font-size:12px;resize:vertical;">' + escapeHtml(data.ai_context) + '</textarea>' +
    '<button class="btn sm" style="margin-top:8px;" onclick="copyPanelContext(this)">复制</button>' : '<p style="color:var(--muted);">暂无 AI 上下文</p>') +
    '</div>' +
    '<div class="panel-actions" style="margin-top:16px;padding-top:14px;border-top:1px solid var(--border);">' +
    '<div style="display:flex;gap:6px;flex-wrap:wrap;">' + buttonsHtml + '</div>' +
    '<div style="margin-top:10px;display:flex;gap:6px;">' +
    (source.path ? '<button class="btn sm" onclick="openSourceDoc(\'' + escapeHtml(source.path) + '\')">源文档</button>' : '') +
    '</div>' +
    '</div>';
}

function transitionTaskFromPanel(newStatus) {
  var title = document.getElementById("taskDetailTitle").textContent;
  var parts = title.split(" ");
  var objId = parts[0];

  _pendingTransition = {
    objId: objId,
    project: "",
    docId: "",
    newStatus: newStatus
  };

  document.getElementById("transitionTitle").textContent = objId + " → " + alias('status', newStatus);
  document.getElementById("transitionReason").value = "";
  document.getElementById("transitionDecision").value = "";
  document.getElementById("transitionAcceptance").value = "";
  document.getElementById("transitionEvidence").value = "";
  document.getElementById("transitionHumanConfirmed").checked = false;
  document.getElementById("transitionModal").classList.add("open");
}

function copyPanelContext(btn) {
  var textarea = document.querySelector(".panel-ai-section textarea");
  if (!textarea) return;
  var text = textarea.value;
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(function() {
      var orig = btn.textContent;
      btn.textContent = "已复制";
      setTimeout(function() { btn.textContent = orig; }, 1500);
    });
  } else {
    textarea.select();
    document.execCommand("copy");
    var orig = btn.textContent;
    btn.textContent = "已复制";
    setTimeout(function() { btn.textContent = orig; }, 1500);
  }
}

var _dragData = null;

function onReqDragStart(e) {
  var card = e.target.closest(".kanban-card");
  if (!card) return;
  _dragData = {
    type: "req",
    objId: card.dataset.objId,
    project: card.dataset.project,
    docId: card.dataset.docId,
    status: card.dataset.status,
    allowed: (card.dataset.allowed || "").split(",").filter(Boolean)
  };
  card.classList.add("dragging");
  e.dataTransfer.effectAllowed = "move";
  e.dataTransfer.setData("text/plain", card.dataset.objId);
}

function onDragOver(e) {
  e.preventDefault();
  e.dataTransfer.dropEffect = "move";
  var col = e.target.closest(".kanban-col");
  if (col) col.classList.add("drag-over");
}

function onDragLeave(e) {
  var col = e.target.closest(".kanban-col");
  if (col) col.classList.remove("drag-over");
}

async function onReqDrop(e, newStatus) {
  e.preventDefault();
  var col = e.target.closest(".kanban-col");
  if (col) col.classList.remove("drag-over");
  document.querySelectorAll(".kanban-card.dragging").forEach(function(c) { c.classList.remove("dragging"); });
  if (!_dragData || _dragData.type !== "req") return;
  var data = _dragData;
  _dragData = null;
  if (data.status === newStatus) return;
  if (data.allowed && data.allowed.length && data.allowed.indexOf(newStatus) < 0) {
    alert("非法状态流转：" + alias('status', data.status) + " → " + alias('status', newStatus) + "。允许流转：" + data.allowed.map(function(s) { return alias('status', s); }).join(" / "));
    return;
  }
  _pendingTransition = data;
  _pendingTransition.newStatus = newStatus;
  document.getElementById("transitionTitle").textContent = data.objId + " · " + alias('status', data.status) + " → " + alias('status', newStatus);
  document.getElementById("transitionReason").value = "";
  document.getElementById("transitionDecision").value = "";
  document.getElementById("transitionAcceptance").value = "";
  document.getElementById("transitionEvidence").value = "";
  document.getElementById("transitionHumanConfirmed").checked = false;
  document.getElementById("transitionModal").classList.add("open");
}

function closeTransitionModal() {
  document.getElementById("transitionModal").classList.remove("open");
  _pendingTransition = null;
}

async function confirmTransition() {
  if (!_pendingTransition) return;
  var data = _pendingTransition;
  var body = {
    status: data.newStatus,
    reason: document.getElementById("transitionReason").value.trim(),
    decision_record: document.getElementById("transitionDecision").value.trim(),
    acceptance_result: document.getElementById("transitionAcceptance").value.trim(),
    closure_evidence: document.getElementById("transitionEvidence").value.trim(),
    human_confirmed: document.getElementById("transitionHumanConfirmed").checked
  };
  try {
    var response = await fetch("/api/requirements/" + encodeURIComponent(data.project) + "/" + encodeURIComponent(data.docId) + "/objects/" + encodeURIComponent(data.objId), {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body)
    });
    if (!response.ok) throw new Error(await response.text());
    closeTransitionModal();
    await loadRequirements();
    await loadPmOverview();
    renderHealthBar();
  renderTaskMetricsPreview(pmOverview ? pmOverview.summary : null);
    loadAuditLog();
  } catch (error) {
    alert("更新失败：" + error.message);
  }
}

async function loadMemos() {
  try {
    var params = new URLSearchParams();
    var searchInput = document.getElementById("memoSearch");
    var filterTypeInput = document.getElementById("memoFilterType");
    var filterStatusInput = document.getElementById("memoFilterStatus");
    var search = searchInput ? searchInput.value : "";
    var filterType = filterTypeInput ? filterTypeInput.value : "";
    var filterStatus = filterStatusInput ? filterStatusInput.value : "";
    if (search) params.set("search", search);
    if (filterType) params.set("type", filterType);
    if (filterStatus) params.set("status", filterStatus);
    if (_memoProjectFilter) params.set("project", _memoProjectFilter);
    var response = await fetch("/api/memos?" + params.toString());
    if (!response.ok) throw new Error(await response.text());
    var data = await response.json();
    _memoData = data.memos || [];
    if (_memoViewMode === "kanban") renderMemoKanban(_memoData);
    else renderMemoList(_memoData);
  } catch (error) {
    document.getElementById("memoKanban").innerHTML = '<div class="error">' + escapeHtml(error.message) + "</div>";
  }
}

function renderMemoKanban(memos) {
  var container = document.getElementById("memoKanban");
  var columns = [
    {key: "open", label: "未处理", color: "#f59e0b"},
    {key: "closed", label: "已关闭", color: "#22c55e"}
  ];
  var grouped = {};
  columns.forEach(function(c) { grouped[c.key] = []; });
  memos.forEach(function(m) {
    if (grouped[m.status]) grouped[m.status].push(m);
    else grouped["open"].push(m);
  });
  var priorityOrder = {"P0": 0, "P1": 1, "P2": 2, "P3": 3};
  Object.values(grouped).forEach(function(arr) {
    arr.sort(function(a, b) {
      var pa = normalizePriority(a.priority) || a.priority;
      var pb = normalizePriority(b.priority) || b.priority;
      return (priorityOrder[pa] ?? 9) - (priorityOrder[pb] ?? 9);
    });
  });

  container.innerHTML = '<div class="kanban">' + columns.map(function(col) {
    var items = grouped[col.key];
    return '<div class="kanban-col" data-status="' + col.key + '" ondragover="onDragOver(event)" ondrop="onMemoDrop(event, \'" + col.key + "\')" ondragleave="onDragLeave(event)">' +
      '<div class="kanban-col-header">' +
      '<div class="kanban-col-dot" style="background:' + col.color + ';"></div>' +
      '<span class="kanban-col-title">' + col.label + '</span>' +
      '<span class="kanban-col-count">' + items.length + '</span>' +
      '</div>' +
      '<div class="kanban-cards">' +
      (items.length === 0 ? '<p style="color:var(--dim);text-align:center;padding:24px 0;">空</p>' : items.map(function(m) {
        var projInfo = PROJECTS[m.project] || {name: m.project};
        var statusLabels = {"open": "未处理", "closed": "已关闭"};
        var statusColor = {"open": "#f59e0b", "closed": "#22c55e"};
        return '<div class="kanban-card" draggable="true" ondragstart="onMemoDragStart(event)" data-entry-id="' + escapeHtml(m.id) + '" data-project="' + escapeHtml(m.project) + '" data-tooltip="1">' +
          '<div class="card-tooltip">' +
          '<div class="ct-row"><span class="ct-label">项目:</span><span class="ct-value">' + escapeHtml(projInfo.name) + '</span></div>' +
          '<div class="ct-row"><span class="ct-label">状态:</span><span class="ct-value">' + escapeHtml(statusLabels[m.status] || m.status) + '</span></div>' +
          '<div class="ct-row"><span class="ct-label">优先级:</span><span class="ct-value">' + escapeHtml(alias('priority', m.priority) || "-") + '</span></div>' +
          '<div class="ct-row"><span class="ct-label">创建:</span><span class="ct-value">' + escapeHtml(m.created_at || "") + '</span></div>' +
          '<div class="ct-row"><span class="ct-label">内容:</span><span class="ct-value">' + escapeHtml(m.content) + '</span></div>' +
          '</div>' +
          '<div class="kanban-card-badges">' +
          '<span class="pill" style="background:rgba(59,130,246,0.15);color:#93c5fd;">' + escapeHtml(projInfo.name) + '</span>' +
          '<span class="pill" style="background:' + statusColor[m.status] + '22;color:' + statusColor[m.status] + ';">' + escapeHtml(statusLabels[m.status] || m.status) + '</span>' +
          '<span class="pill">' + escapeHtml(alias('priority', m.priority) || "-") + '</span>' +
          '</div>' +
          '<p class="kanban-card-title">' + escapeHtml(m.content) + '</p>' +
          '<p class="kanban-card-meta">' + escapeHtml(m.created_at || "") + (m.close_reason ? ' · ' + escapeHtml(m.close_reason) : '') + '</p>' +
          '<div class="kanban-card-actions">' +
          '<button class="btn sm copy-btn" onclick="copyTaskPrompt(this)" data-copy="' + escapeHtml(btoa(unescape(encodeURIComponent(
            '请处理以下 task-base 备忘：\n' +
            '项目: ' + m.project + '\n' +
            'ID: ' + m.id + '\n' +
            '状态: ' + (statusLabels[m.status] || m.status) + '\n' +
            '内容: ' + m.content + '\n' +
            '事实源: ' + m.path + '\n'
          )))) + '" title="复制备忘信息给AI">⎘</button>' +
          '<button class="btn sm" onclick="cycleMemoStatus(\'' + escapeHtml(m.project) + "','" + escapeHtml(m.id) + "','" + escapeHtml(m.status) + "')\">↻</button>" +
          '</div></div>';
      }).join('')) +
      '</div></div>';
  }).join('') + '</div>';
}

function onMemoDragStart(e) {
  var card = e.target.closest(".kanban-card");
  if (!card) return;
  _dragData = {
    type: "memo",
    entryId: card.dataset.entryId,
    project: card.dataset.project
  };
  card.classList.add("dragging");
  e.dataTransfer.effectAllowed = "move";
  e.dataTransfer.setData("text/plain", card.dataset.entryId);
}

function renderMemoList(memos) {
  var container = document.getElementById("memoList");
  if (memos.length === 0) {
    container.innerHTML = '<div style="color:var(--muted);padding:16px;text-align:center;">暂无匹配的 task-base 备忘。</div>';
    return;
  }
  var statusLabels = {"open": "未处理", "closed": "已关闭"};
  var statusColors = {"open": "#f59e0b", "closed": "#22c55e"};
  var priorityOrder = {"P0": 0, "P1": 1, "P2": 2, "P3": 3};
  var sorted = memos.slice().sort(function(a, b) {
    var pa = normalizePriority(a.priority) || a.priority;
    var pb = normalizePriority(b.priority) || b.priority;
    return (priorityOrder[pa] ?? 9) - (priorityOrder[pb] ?? 9);
  });
  container.innerHTML = sorted.map(function(m) {
    var projInfo = PROJECTS[m.project] || {name: m.project};
    var sColor = statusColors[m.status] || "#64748b";
    return '<div class="memo-list-item">' +
      '<div class="memo-badges">' +
      '<span class="pill" style="background:rgba(59,130,246,0.15);color:#93c5fd;">' + escapeHtml(projInfo.name) + '</span>' +
      '<span class="pill" style="background:' + sColor + '22;color:' + sColor + ';">' + escapeHtml(statusLabels[m.status] || m.status) + '</span>' +
      '<span class="pill">' + escapeHtml(alias('priority', m.priority) || "-") + '</span>' +
      '</div>' +
      '<div class="memo-id">' + escapeHtml((m.id || "").replace(/^MEMO-\d{2}(\d{2})/, "$1")) + '</div>' +
      '<div class="memo-content">' + escapeHtml(m.content) + '</div>' +
      '<div class="memo-meta">' + escapeHtml(m.created_at || "") + (m.close_reason ? ' · ' + escapeHtml(m.close_reason) : '') + '</div>' +
      '<div class="memo-actions">' +
      '<button class="btn sm" onclick="cycleMemoStatus(\'' + escapeHtml(m.project) + "','" + escapeHtml(m.id) + "','" + escapeHtml(m.status) + "')\">↻</button>" +
      '</div></div>';
  }).join('');
}

async function onMemoDrop(e, newStatus) {
  e.preventDefault();
  var col = e.target.closest(".kanban-col");
  if (col) col.classList.remove("drag-over");
  document.querySelectorAll(".kanban-card.dragging").forEach(function(c) { c.classList.remove("dragging"); });
  if (!_dragData || _dragData.type !== "memo") return;
  var data = _dragData;
  _dragData = null;
  if (newStatus === "closed") {
    var reason = prompt("关闭备忘的原因 / 处理结果：");
    if (!reason) return;
    await updateTaskBaseMemo(data.project, data.entryId, {status: newStatus, close_reason: reason});
  } else {
    await updateTaskBaseMemo(data.project, data.entryId, {status: newStatus});
  }
}

async function cycleMemoStatus(project, entryId, currentStatus) {
  var nextStatus = currentStatus === "open" ? "closed" : "open";
  var body = {status: nextStatus};
  if (nextStatus === "closed") {
    var reason = prompt("关闭备忘的原因 / 处理结果：");
    if (!reason) return;
    body.close_reason = reason;
  }
  await updateTaskBaseMemo(project, entryId, body);
}

async function updateTaskBaseMemo(project, entryId, body) {
  try {
    var response = await fetch("/api/pm/task-base/memos/" + encodeURIComponent(project) + "/" + encodeURIComponent(entryId), {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body)
    });
    if (!response.ok) throw new Error(await response.text());
    await loadTaskBase();
  } catch (error) {
    alert("更新失败：" + error.message);
  }
}

function openAddMemoModal() {
  var sel = document.getElementById("memoAddProject");
  sel.innerHTML = Object.keys(PROJECTS).map(function(key) {
    return '<option value="' + key + '">' + escapeHtml(PROJECTS[key].name) + "</option>";
  }).join("");
  if (_memoProjectFilter) sel.value = _memoProjectFilter;
  document.getElementById("memoAddDate").value = new Date().toISOString().slice(0, 10);
  document.getElementById("memoAddType").value = "TODO";
  document.getElementById("memoAddPriority").value = "P1";
  document.getElementById("memoAddGroup").value = "";
  document.getElementById("memoAddContent").value = "";
  document.getElementById("addMemoModal").classList.add("open");
}

function closeAddMemoModal() {
  document.getElementById("addMemoModal").classList.remove("open");
}

async function submitAddMemo() {
  var project = document.getElementById("memoAddProject").value;
  var body = {
    date: document.getElementById("memoAddDate").value,
    type: document.getElementById("memoAddType").value,
    priority: document.getElementById("memoAddPriority").value,
    group_title: document.getElementById("memoAddGroup").value,
    content: document.getElementById("memoAddContent").value
  };
  if (!body.content) { alert("请填写内容"); return; }
  try {
    var response = await fetch("/api/memos/" + encodeURIComponent(project), {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body)
    });
    if (!response.ok) throw new Error(await response.text());
    closeAddMemoModal();
    await loadMemos();
  } catch (error) {
    alert("创建失败：" + error.message);
  }
}

function openEditMemoModal(project, entryId, type, status) {
  _editingMemoId = entryId;
  _editingMemoProject = project;
  document.getElementById("memoEditType").value = type;
  document.getElementById("memoEditStatus").value = status;
  var memo = (_memoData || []).find(function(m) { return m.id === entryId && m.project === project; });
  document.getElementById("memoEditContent").value = memo ? memo.content : "";
  document.getElementById("editMemoModal").classList.add("open");
}

function closeEditMemoModal() {
  document.getElementById("editMemoModal").classList.remove("open");
  _editingMemoId = null;
  _editingMemoProject = null;
}

async function submitEditMemo() {
  if (!_editingMemoId || !_editingMemoProject) return;
  var body = {
    type: document.getElementById("memoEditType").value,
    status: document.getElementById("memoEditStatus").value,
    content: document.getElementById("memoEditContent").value
  };
  try {
    var response = await fetch("/api/memos/" + encodeURIComponent(_editingMemoProject) + "/" + encodeURIComponent(_editingMemoId), {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body)
    });
    if (!response.ok) throw new Error(await response.text());
    closeEditMemoModal();
    await loadMemos();
  } catch (error) {
    alert("更新失败：" + error.message);
  }
}

function openArchiveMemoModal(project, entryId) {
  _archivingMemoId = entryId;
  _archivingMemoProject = project;
  document.getElementById("archiveMemoModal").classList.add("open");
}

function closeArchiveMemoModal() {
  document.getElementById("archiveMemoModal").classList.remove("open");
  _archivingMemoId = null;
  _archivingMemoProject = null;
}

async function confirmArchiveMemo() {
  if (!_archivingMemoId || !_archivingMemoProject) return;
  try {
    var response = await fetch("/api/memos/" + encodeURIComponent(_archivingMemoProject) + "/" + encodeURIComponent(_archivingMemoId), {
      method: "DELETE"
    });
    if (!response.ok) throw new Error(await response.text());
    closeArchiveMemoModal();
    await loadMemos();
  } catch (error) {
    alert("归档失败：" + error.message);
  }
}

function toggleDocView() {
  _docViewMode = _docViewMode === "raw" ? "md" : "raw";
  document.getElementById("docViewToggle").textContent = _docViewMode === "raw" ? "Markdown 视图" : "原始视图";
  var viewer = document.getElementById("docViewer");
  viewer.classList.toggle("raw", _docViewMode === "raw");
  viewer.classList.toggle("md", _docViewMode === "md");
  if (_currentDocContent) renderDocContent(_currentDocContent);
}

function renderDocContent(content) {
  var viewer = document.getElementById("docViewer");
  if (_docViewMode === "md" && typeof marked !== "undefined") {
    viewer.innerHTML = marked.parse(content);
  } else {
    viewer.textContent = content;
  }
}

async function loadDoc(path) {
  var viewer = document.getElementById("docViewer");
  _currentDocPath = path;
  viewer.textContent = "读取中...";
  try {
    var response = await fetch("/api/doc?path=" + encodeURIComponent(path));
    if (!response.ok) throw new Error(await response.text());
    var payload = await response.json();
    _currentDocContent = payload.content;
    renderDocContent(_currentDocContent);
  } catch (error) {
    viewer.innerHTML = '<div class="error">' + escapeHtml(error.message) + "</div>";
    _currentDocContent = null;
  }
}

async function loadRulesAudit() {
  var summary = document.getElementById("rulesAuditSummary");
  var list = document.getElementById("rulesAuditList");
  summary.innerHTML = '<div class="card"><p>复核中...</p></div>';
  list.innerHTML = "";
  try {
    var response = await fetch("/api/rules/audit");
    if (!response.ok) throw new Error(await response.text());
    var audit = await response.json();
    summary.innerHTML =
      '<div class="card"><h3>项目数</h3><div class="metric">' + audit.summary.projects + '</div></div>' +
      '<div class="card"><h3>通过</h3><div class="metric" style="color:var(--green)">' + audit.summary.pass + '</div></div>' +
      '<div class="card"><h3>警告</h3><div class="metric" style="color:var(--yellow)">' + audit.summary.warn + '</div></div>' +
      '<div class="card"><h3>失败</h3><div class="metric" style="color:var(--red)">' + audit.summary.fail + "</div></div>";
    list.innerHTML = audit.results.map(function(item) {
      var findings = item.findings.length ? item.findings.map(function(finding) {
        return '<div style="margin-top:10px;padding:10px;border:1px solid var(--border);border-radius:10px;background:rgba(15,23,42,.55);">' +
          '<span class="pill ' + (finding.severity === "high" ? "" : finding.severity === "medium" ? "current" : "next") + '">' + escapeHtml(alias('severity', finding.severity)) + "</span>" +
          " <strong>" + escapeHtml(finding.title) + "</strong>" +
          '<p style="margin:6px 0;color:var(--muted);">' + escapeHtml(finding.detail) + "</p>" +
          '<p style="margin:0;color:var(--dim);">建议：' + escapeHtml(finding.suggestion) + "</p></div>";
      }).join("") : '<p style="color:var(--muted);">未发现问题。</p>';
      return '<div class="card"><h3>' + escapeHtml(item.name || item.project) + ' <span class="pill ' + (item.status === "pass" ? "done" : item.status === "warn" ? "current" : "") + '">' + escapeHtml(alias('audit', item.status)) + "</span></h3>" +
        "<p>得分：" + item.score + " · 有效行数：" + item.line_count + " · " + escapeHtml(item.path) + "</p>" +
        findings + "</div>";
    }).join("");
  } catch (error) {
    summary.innerHTML = '<div class="error">' + escapeHtml(error.message) + "</div>";
  }
}

function startAutoRefresh() {
  _autoRefreshTimer = setInterval(async function() {
    try {
      await loadData(false);
      var activeTab = document.querySelector("section.active");
      if (activeTab && activeTab.id === "actions") {
        var taskBaseArea = document.getElementById("actionTaskBaseArea");
        if (taskBaseArea && !taskBaseArea.classList.contains("hidden")) {
          await loadTaskBase();
        }
      }
      if (activeTab && activeTab.id === "settings") {
        var setTab = document.querySelector("#settings .tab.active");
        if (setTab && setTab.dataset.settab === "panorama") {
          await loadPanorama();
        }
      }
    } catch (e) {}
  }, 300000);
}

async function manualRefresh() {
  var btn = document.querySelector(".health-bar-refresh");
  if (btn) btn.classList.add("spinning");
  try {
    await loadData(true);
    var activeTab = document.querySelector("section.active");
    if (activeTab && activeTab.id === "actions") {
      var taskBaseArea = document.getElementById("actionTaskBaseArea");
      if (taskBaseArea && !taskBaseArea.classList.contains("hidden")) {
        await loadTaskBase();
      }
    }
    if (activeTab && activeTab.id === "settings") {
      var setTab = document.querySelector("#settings .tab.active");
      if (setTab && setTab.dataset.settab === "panorama") {
        await loadPanorama();
      }
    }
    renderHealthBar();
    renderTaskMetricsPreview(pmOverview ? pmOverview.summary : null);
    renderMemoListOverview();
    renderRecentChanges();
  } catch (e) {}
  if (btn) btn.classList.remove("spinning");
}

var _mermaidInitialized = false;

function initMermaid() {
  if (_mermaidInitialized) return;
  if (typeof mermaid !== 'undefined') {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      themeVariables: {
        primaryColor: '#1e293b',
        primaryTextColor: '#f1f5f9',
        primaryBorderColor: '#334155',
        lineColor: '#64748b',
        secondaryColor: '#0f172a',
        tertiaryColor: '#1e293b',
        fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif',
        fontSize: '13px'
      },
      flowchart: { curve: 'basis', padding: 20 }
    });
    _mermaidInitialized = true;
  }
}

async function loadPanorama() {
  initMermaid();
  try {
    var resp = await fetch('/api/panorama');
    if (!resp.ok) throw new Error(await resp.text());
    var data = await resp.json();

    var flowEl = document.getElementById('mermaidDataFlow');
    var depEl = document.getElementById('mermaidDependency');

    if (typeof mermaid !== 'undefined') {
      var uid = Date.now();
      try {
        flowEl.innerHTML = '<pre class="mermaid" id="mf' + uid + '">' + data.data_flow_mermaid + '</pre>';
        await mermaid.run({ nodes: [document.getElementById('mf' + uid)] });
      } catch(e) {
        flowEl.innerHTML = '<div class="error">数据流图渲染失败：' + escapeHtml(e.message || String(e)) + '</div>';
      }
      try {
        depEl.innerHTML = '<pre class="mermaid" id="md' + uid + '">' + data.dependency_mermaid + '</pre>';
        await mermaid.run({ nodes: [document.getElementById('md' + uid)] });
      } catch(e) {
        depEl.innerHTML = '<div class="error">依赖图渲染失败：' + escapeHtml(e.message || String(e)) + '</div>';
      }
    } else {
      flowEl.innerHTML = '<pre style="color:var(--muted);font-size:12px;white-space:pre-wrap;">' + escapeHtml(data.data_flow_mermaid) + '</pre>';
      depEl.innerHTML = '<pre style="color:var(--muted);font-size:12px;white-space:pre-wrap;">' + escapeHtml(data.dependency_mermaid) + '</pre>';
    }

    document.getElementById('systemTable').innerHTML = data.systems.map(function(s) {
      var normPrio2 = normalizePriority(s.priority);
      var prioColor2 = normPrio2 ? (PRIORITY_COLORS[normPrio2] || 'var(--dim)') : 'var(--dim)';
      return '<tr><td>' + s.id + '</td><td>' + escapeHtml(s.name) + '</td><td>' + escapeHtml(s.desc) +
        '</td><td><span class="pill">' + escapeHtml(s.project) + '</span></td>' +
        '<td><span style="color:' + prioColor2 + '">' + escapeHtml(normPrio2 || s.priority) + '</span></td>' +
        '<td><span class="pill current">' + escapeHtml(s.status) + '</span></td>' +
        '<td style="color:var(--muted)">' + escapeHtml(s.dep) + '</td></tr>';
    }).join('');

    document.getElementById('decisionTimeline').innerHTML = data.decisions.map(function(d) {
      var statusClass = d.status === 'Accepted' ? 'done' : d.status === 'Proposed' ? 'next' : '';
      return '<div class="step ' + statusClass + '" style="padding:10px;">' +
        '<strong style="color:var(--cyan)">' + escapeHtml(d.id) + '</strong>' +
        '<div>' + escapeHtml(d.title) + '</div>' +
        '<span class="pill ' + statusClass + '">' + escapeHtml(alias('decision', d.status)) + '</span>' +
        (d.date ? '<span style="color:var(--dim);font-size:12px;margin-left:8px;">' + escapeHtml(d.date) + '</span>' : '') +
        '</div>';
    }).join('');

    var dashResp = await fetch('/api/dashboard');
    var dash = dashResp.ok ? await dashResp.json() : {};
    document.getElementById('panoramaProjects').innerHTML = (dash.project_rules || []).map(function(p) {
      var hasAll = p.exists && p.has_docs_index && p.has_compression;
      return '<div class="panorama-card" style="border-left:3px solid ' + (hasAll ? 'var(--green)' : p.exists ? 'var(--yellow)' : 'var(--red)') + '">' +
        '<div class="pname">' + escapeHtml(p.name || p.project) + '</div>' +
        '<div class="prole">' + escapeHtml(p.role || '') + '</div>' +
        '<div class="pstatus">' + (p.exists ? '✅ 规则' : '❌ 规则') + ' ' +
        (p.has_docs_index ? '✅ 索引' : '❌ 索引') + ' ' +
        (p.has_compression ? '✅ 压缩保护' : '❌ 压缩保护') + '</div>' +
        '<button class="readme-btn" onclick="toggleReadme(\'' + p.project + '\', this)">📖 README</button>' +
        '<div class="readme-content" id="readme-' + p.project + '" style="display:none;"></div></div>';
    }).join('');
  } catch (error) {
    document.getElementById('mermaidDataFlow').innerHTML = '<div class="error">' + escapeHtml(error.message) + '</div>';
  }
}

async function toggleReadme(project, btn) {
  var el = document.getElementById('readme-' + project);
  if (!el) return;
  if (el.style.display !== 'none') {
    el.style.display = 'none';
    btn.textContent = '📖 README';
    return;
  }
  if (el.dataset.loaded === '1') {
    el.style.display = 'block';
    btn.textContent = '📖 收起';
    return;
  }
  try {
    var resp = await fetch('/api/readme/' + project);
    if (!resp.ok) throw new Error(await resp.text());
    var data = await resp.json();
    if (!data.exists) {
      el.innerHTML = '<div style="color:var(--muted);padding:8px;">暂无 README.md</div>';
    } else if (typeof marked !== 'undefined') {
      el.innerHTML = '<div class="markdown-body">' + marked.parse(data.content) + '</div>';
    } else {
      el.innerHTML = '<pre style="white-space:pre-wrap;font-size:13px;color:var(--muted);">' + escapeHtml(data.content) + '</pre>';
    }
    el.dataset.loaded = '1';
    el.style.display = 'block';
    btn.textContent = '📖 收起';
  } catch(e) {
    el.innerHTML = '<div class="error">' + escapeHtml(e.message) + '</div>';
    el.style.display = 'block';
  }
}

async function loadAuditLog() {
  var el = document.getElementById("auditLogList");
  if (!el) return;
  try {
    var resp = await fetch("/api/audit-log?limit=50");
    if (!resp.ok) return;
    var data = await resp.json();
    var logs = data.logs || [];
    if (logs.length === 0) {
      el.innerHTML = '<div style="color:var(--muted);padding:12px;text-align:center;">暂无操作记录</div>';
      return;
    }
    var actionLabels = {
      "update_object": "✏️ 更新对象状态",
      "create_memo": "➕ 新增备忘",
      "update_memo": "✏️ 更新备忘",
      "delete_memo": "🗑️ 删除备忘"
    };
    el.innerHTML = '<table style="width:100%;border-collapse:collapse;font-size:13px;"><thead><tr><th style="width:160px;">时间</th><th style="width:140px;">操作</th><th style="width:180px;">目标</th><th>详情</th></tr></thead><tbody>' +
      logs.reverse().map(function(log) {
        return '<tr>' +
          '<td style="color:var(--dim);white-space:nowrap;">' + escapeHtml(log.timestamp.replace("T", " ").substring(0, 19)) + '</td>' +
          '<td>' + (actionLabels[log.action] || escapeHtml(log.action)) + '</td>' +
          '<td style="color:var(--cyan);">' + escapeHtml(log.target) + '</td>' +
          '<td style="color:var(--muted);">' + escapeHtml(log.detail || "") + '</td>' +
          '</tr>';
      }).join("") +
      '</tbody></table>';
  } catch(e) {}
}

function openCommandMenu() {
  var overlay = document.getElementById("commandMenuOverlay");
  if (!overlay) return;
  overlay.classList.add("open");
  document.getElementById("commandInput").value = "";
  document.getElementById("commandInput").focus();
  document.getElementById("commandResults").innerHTML = '<p style="color:var(--muted);text-align:center;padding:24px;">输入关键词开始搜索</p>';
}

function closeCommandMenu() {
  var overlay = document.getElementById("commandMenuOverlay");
  if (overlay) overlay.classList.remove("open");
}

function handleCommandSearch(query) {
  if (!query || query.length < 2) {
    document.getElementById("commandResults").innerHTML = '<p style="color:var(--muted);text-align:center;padding:24px;">至少输入 2 个字符</p>';
    return;
  }

  var results = { tasks: [], docs: [], memos: [] };
  var q = query.toLowerCase();

  if (_reqData) {
    _reqData.forEach(function(req) {
      var match = (req.id || "").toLowerCase().indexOf(q) >= 0 ||
                  (req.title || "").toLowerCase().indexOf(q) >= 0;
      if (match) {
        results.tasks.push({ type: "task", id: req.id, title: req.title, path: req.path, status: req.status });
      }
      (req.exec_objects || []).forEach(function(obj) {
        if ((obj.id || "").toLowerCase().indexOf(q) >= 0 || (obj.title || "").toLowerCase().indexOf(q) >= 0) {
          results.tasks.push({ type: "task", id: obj.id, title: obj.title, path: req.path, status: obj.status });
        }
      });
    });
  }

  if (state && state.doc_links) {
    state.doc_links.forEach(function(doc) {
      if ((doc.id || "").toLowerCase().indexOf(q) >= 0 ||
          (doc.title || "").toLowerCase().indexOf(q) >= 0 ||
          (doc.path || "").toLowerCase().indexOf(q) >= 0) {
        results.docs.push({ id: doc.id, title: doc.title, path: doc.path });
      }
    });
  }

  if (_memoData) {
    _memoData.forEach(function(memo) {
      if ((memo.id || "").toLowerCase().indexOf(q) >= 0 ||
          (memo.content || "").toLowerCase().indexOf(q) >= 0) {
        results.memos.push({ id: memo.id, content: memo.content, path: memo.path, project: memo.project });
      }
    });
  }

  renderCommandResults(results);
}

function renderCommandResults(results) {
  var html = '';

  if (results.tasks.length > 0) {
    html += '<div class="command-group"><div class="command-group-label">任务 (' + results.tasks.length + ')</div>';
    results.tasks.slice(0, 5).forEach(function(item) {
      html += '<div class="command-item" onclick="handleCommandResultClick(\'task\', \'' + escapeAttr(item.id) + '\', \'' + escapeAttr(item.path || "") + '\')">' +
        '<span class="command-item-icon">📋</span>' +
        '<span class="command-item-title">' + escapeHtml(item.id) + ' ' + escapeHtml(item.title || "") + '</span>' +
        '<span class="command-item-meta">' + escapeHtml(alias('status', item.status)) + '</span>' +
        '</div>';
    });
    if (results.tasks.length > 5) {
      html += '<div class="command-item" style="color:var(--muted);justify-content:center;">...还有 ' + (results.tasks.length - 5) + ' 个结果</div>';
    }
    html += '</div>';
  }

  if (results.docs.length > 0) {
    html += '<div class="command-group"><div class="command-group-label">文档 (' + results.docs.length + ')</div>';
    results.docs.slice(0, 3).forEach(function(item) {
      html += '<div class="command-item" onclick="openSourceDoc(\'' + escapeAttr(item.path) + '\')">' +
        '<span class="command-item-icon">📄</span>' +
        '<span class="command-item-title">' + escapeHtml(item.id) + ' ' + escapeHtml(item.title || "") + '</span>' +
        '<span class="command-item-meta">' + escapeHtml(item.path) + '</span>' +
        '</div>';
    });
    html += '</div>';
  }

  if (results.memos.length > 0) {
    html += '<div class="command-group"><div class="command-group-label">备忘 (' + results.memos.length + ')</div>';
    results.memos.slice(0, 3).forEach(function(item) {
      html += '<div class="command-item" onclick="openSourceDoc(\'' + escapeAttr(item.path) + '\')">' +
        '<span class="command-item-icon">📝</span>' +
        '<span class="command-item-title">' + escapeHtml(item.id) + ' ' + escapeHtml((item.content || "").substring(0, 40)) + '</span>' +
        '</div>';
    });
    html += '</div>';
  }

  if (!html) {
    html = '<p style="color:var(--muted);text-align:center;padding:24px;">未找到匹配结果</p>';
  }

  document.getElementById("commandResults").innerHTML = html;
}

function handleCommandResultClick(type, id, path) {
  closeCommandMenu();
  if (type === "task") {
    var parts = (path || "").split("/");
    var project = "";
    var docId = "";
    if (parts.length >= 4) {
      project = parts[parts.length - 3];
      docId = parts[parts.length - 2];
    }
    if (project && docId) {
      loadTaskDetail(project, docId, id, "action");
    } else {
      setTab("actions");
    }
  }
}

var _commandSearchTimer = null;

function init() {
  document.addEventListener("keydown", function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      var overlay = document.getElementById("commandMenuOverlay");
      if (overlay && overlay.classList.contains("open")) {
        closeCommandMenu();
      } else {
        openCommandMenu();
      }
    }
    if (e.key === "Escape") {
      closeCommandMenu();
    }
  });

  var cmdInput = document.getElementById("commandInput");
  if (cmdInput) {
    cmdInput.addEventListener("input", function() {
      clearTimeout(_commandSearchTimer);
      _commandSearchTimer = setTimeout(function() {
        handleCommandSearch(cmdInput.value);
      }, 300);
    });
  }

  loadConfig().then(function() {
    buildProjectSelector("reqProjectSelector", "", selectReqProject);
    buildProjectSelector("memoProjectSelector", "", selectMemoProject);
    loadData().catch(function(error) {
      document.body.innerHTML = '<div class="page"><div class="error">加载失败：' + escapeHtml(error.message) + "</div></div>";
    });
    startAutoRefresh();
  });
}

init();
