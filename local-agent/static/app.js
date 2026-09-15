"use strict";

const state = { project: null, rows: [], scripts: [], approvedScript: null, route: "avatar", media: [], busy: false, domainId: "finance", styleId: "editorial-proof" };
const domainOptions = [
  ["custom", "Ngách tùy chỉnh"], ["finance", "Tài chính & đầu tư"], ["real-estate", "Bất động sản"],
  ["education", "Giáo dục & đào tạo"], ["beauty", "Làm đẹp & thẩm mỹ"], ["healthcare", "Sức khỏe"],
  ["fnb", "F&B & dịch vụ"], ["technology", "Công nghệ & AI"], ["ecommerce", "Bán lẻ & TMĐT"]
];
const editStyleOptions = [
  ["editorial-proof", "Editorial Proof"], ["clean-expert", "Clean Expert"], ["warm-story", "Warm Story"],
  ["luxury-minimal", "Luxury Minimal"], ["bold-social", "Bold Social"], ["tiktok-creator", "TikTok Creator"],
  ["screen-demo", "Screen Demo"], ["data-kinetic", "Data Kinetic"], ["visual-metaphor", "Visual Metaphor"],
  ["documentary-reveal", "Documentary Reveal"], ["swiss-pulse", "Swiss Pulse"], ["velvet-standard", "Velvet Standard"],
  ["deconstructed", "Deconstructed"], ["maximalist-type", "Maximalist Type"], ["data-drift", "Data Drift"],
  ["soft-signal", "Soft Signal"], ["folk-frequency", "Folk Frequency"], ["shadow-cut", "Shadow Cut"]
];
const selectOptions = (items, selected) => items.map(([value, label]) => `<option value="${esc(value)}" ${value === selected ? "selected" : ""}>${esc(label)}</option>`).join("");
const modes = {
  full: ["research", "select", "script", "heygen", "align", "story", "assets", "edit", "qa", "content", "publish"],
  script: ["script", "heygen", "align", "story", "assets", "edit", "qa", "content", "publish"],
  edit: ["align", "story", "assets", "edit", "qa", "content", "publish"],
  publish: ["content", "publish"]
};
let currentMode = "full";
let currentView = "workflow";
const stageEls = [...document.querySelectorAll(".stage")];

const details = {
  research: ["Bước 01 · Discovery", "Research đa nền tảng", "Chọn ngành, từ khóa, nền tảng và danh sách kênh đối thủ. Chế độ Live đọc dữ liệu công khai; Demo giúp thử luồng ngay."],
  select: ["Bước 02 · Strategy gate", "Duyệt video tham chiếu", "Chọn một video sau khi so sánh nguồn, link gốc, chỉ số tương tác và lý do viral."],
  script: ["Bước 03 · Script gate", "Ba kịch bản hoặc nhập kịch bản", "Agent tạo ba hướng nguyên bản. Bạn sửa trực tiếp và chỉ kịch bản bấm Duyệt mới đi tiếp."],
  heygen: ["Bước 04 · Production route", "Avatar HeyGen hoặc No-face", "Avatar hỗ trợ nhiều look luân phiên; No-face tạo kế hoạch visual theo từng beat. Cả hai hội tụ tại edit."],
  align: ["Bước 05 · Source", "Nhận video gốc", "Dùng video từ HeyGen, no-face hoặc tải video có sẵn để chạy luồng edit-only."],
  story: ["Bước 06 · Editorial logic", "Voice → claim → visual proof", "Technical claim dùng chart/diagram; sự kiện thật dùng footage thật; stock chỉ làm bối cảnh."],
  assets: ["Bước 07 · Visual evidence", "Chart, real-world và stock B-roll", "Lưu nguồn và license; không sao chép watermark, chart hoặc hình riêng của đối thủ."],
  edit: ["Bước 08 · Multi-style Edit", "Tạo phiếu edit và feedback phiên bản", "Phiếu EDIT_REQUEST.md và edit_plan.json là hợp đồng đầu vào cho skill multi-style-video-editor."],
  qa: ["Bước 09 · Quality gate", "QA final", "Xem toàn video, kiểm tra subtitle, proof, flash frame, voice/BGM/SFX và thời lượng."],
  content: ["Bước 10 · Distribution prep", "Nội dung đăng bài", "Tạo caption riêng theo nền tảng, hashtag, music credit và disclaimer."],
  publish: ["Bước 11 · External action", "Đăng bài hoặc bỏ qua", "Mặc định Skip. Đăng thật luôn có xác nhận cuối và dùng publisher theo từng nền tảng."]
};

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, ch => ({"&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"})[ch]);
}

function toast(message, error = false) {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.style.background = error ? "#ffd7dc" : "#eefbd6";
  el.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => el.classList.remove("show"), 2800);
}

async function api(path, options = {}) {
  const headers = {"X-BrandFlow-Agent": "1", ...(options.headers || {})};
  let body = options.body;
  if (body && !(body instanceof Blob) && typeof body !== "string") {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(body);
  }
  const response = await fetch(path, {...options, headers, body});
  const data = await response.json().catch(() => ({ok:false, error:`HTTP ${response.status}`}));
  if (!response.ok || data.ok === false) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}

async function withBusy(button, label, work) {
  if (state.busy) return;
  state.busy = true;
  const old = button ? button.textContent : "";
  if (button) { button.disabled = true; button.textContent = label; }
  try { return await work(); }
  catch (error) { toast(error.message, true); throw error; }
  finally { state.busy = false; if (button) { button.disabled = false; button.textContent = old; } }
}

async function pollJob(jobId, statusId) {
  while (true) {
    const {job} = await api(`/api/jobs/${encodeURIComponent(jobId)}`);
    const status = document.getElementById(statusId);
    if (status) status.innerHTML = `${esc(job.message)}<div class="jobbar"><i style="width:${Number(job.progress || 0)}%"></i></div>`;
    if (job.status === "done") return job.result;
    if (["error", "interrupted"].includes(job.status)) throw new Error(job.message || "Job thất bại");
    await new Promise(resolve => setTimeout(resolve, 1200));
  }
}

function updateProject(project) {
  state.project = project;
  document.getElementById("projectBadge").textContent = project ? `Project · ${project.id}` : "Chưa tạo project";
}

async function ensureProject(title = "Personal Brand Video", selectedVideo = null) {
  if (state.project) return state.project;
  const data = await api("/api/projects", {method:"POST", body:{title, selected_video:selectedVideo, domain_id:state.domainId, style_id:state.styleId}});
  updateProject(data.project);
  return data.project;
}

function setStage(key, status, label) {
  const el = stageEls.find(item => item.dataset.step === key);
  if (!el) return;
  el.dataset.state = status;
  const badge = el.querySelector(".status");
  if (badge) badge.textContent = label;
}

function workShell(kicker, title, desc, body) {
  return `<div class="work-head"><div><div class="eyebrow">${esc(kicker)}</div><h3>${esc(title)}</h3><p>${esc(desc)}</p></div></div><div class="work-body">${body}</div>`;
}

function renderWorkbench(key) {
  const box = document.getElementById("workbench");
  if (key === "research") return renderResearch(box);
  if (key === "script") return renderScripts(box);
  if (key === "heygen") return renderProduction(box);
  if (key === "align") return renderUpload(box);
  if (key === "edit") return renderEdit(box);
  if (key === "qa") return renderQa(box);
  if (key === "publish") return renderPublish(box);
  const item = details[key];
  box.innerHTML = workShell(item[0], item[1], item[2], `<div class="callout">Bước này dùng workflow Finance đã kiểm chứng, được cấu hình theo domain pack và skill <strong>multi-style-video-editor</strong>. Artifact và trạng thái luôn lưu theo project.</div>`);
}

function renderDetail(key) {
  const item = details[key];
  setView("workflow");
  stageEls.forEach(el => el.classList.toggle("selected", el.dataset.step === key));
  document.getElementById("workflowTitle").textContent = item[1];
  document.getElementById("workflowDesc").textContent = item[2];
  renderWorkbench(key);
  document.getElementById("workbench").scrollIntoView({behavior:"smooth", block:"start"});
}

function setView(view, updateHash = true) {
  currentView = view === "map" ? "map" : "workflow";
  document.getElementById("workflowView").classList.toggle("hidden-pane", currentView !== "workflow");
  document.getElementById("mapView").classList.toggle("hidden-pane", currentView !== "map");
  document.getElementById("workflowSidebar").classList.toggle("hidden-pane", currentView !== "workflow");
  document.querySelectorAll(".view-tab").forEach(button => {
    const active = button.dataset.view === currentView;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
  if (updateHash) history.replaceState(null, "", currentView === "map" ? "#map" : "#workflow");
  document.querySelector("main")?.scrollTo({top:0, behavior:"smooth"});
}

function renderResearch(box) {
  box.innerHTML = workShell("Thao tác bước 01", "Research đối thủ", "Demo dùng dữ liệu mẫu; Live quét các URL kênh công khai bạn cung cấp.", `
    <div class="toolbar">
      <label class="choice"><input type="checkbox" name="platform" checked value="facebook"> Facebook</label>
      <label class="choice"><input type="checkbox" name="platform" checked value="tiktok"> TikTok</label>
      <label class="choice"><input type="checkbox" name="platform" checked value="youtube"> YouTube</label>
      <label class="field-label">Chế độ<select class="field" id="researchMode"><option value="demo">Demo nhanh</option><option value="live">Live từ URL kênh</option></select></label>
      <label class="field-label">Viết kịch bản<select class="field" id="scriptMode"><option value="demo">Mẫu thử</option><option value="live">LLM live</option></select></label>
      <label class="field-label">Ngành/ngách<select class="field" id="researchIndustry">${selectOptions(domainOptions, state.domainId)}</select></label>
      <label class="field-label">Từ khóa<input class="field" id="researchKeyword" placeholder="VD: liquidity, stop loss"></label>
      <label class="field-label">Xếp hạng<select class="field" id="researchSort"><option value="viral">Viral score</option><option value="views">Lượt xem</option><option value="engagement">Tương tác</option></select></label>
    </div>
    <label class="field-label">URL kênh đối thủ — mỗi dòng một URL<textarea id="channelUrls" style="min-height:92px" placeholder="https://www.youtube.com/@kenh-doi-thu/videos&#10;https://www.tiktok.com/@kenh-doi-thu"></textarea></label>
    <div class="help">Facebook/TikTok có thể giới hạn dữ liệu công khai hoặc yêu cầu phiên đăng nhập. Agent không vượt qua quyền riêng tư của nền tảng.</div>
    <div class="toolbar" style="margin-top:14px"><button class="mini-btn primary-action" id="researchRun">Chạy research</button></div>
    <div id="researchStatus" class="status-line"></div>
    <div id="researchResult" class="empty-result">Chọn nền tảng, ngành và từ khóa rồi bấm <strong>Chạy research</strong>.</div>`);
  document.getElementById("researchRun").addEventListener("click", runResearch);
}

async function runResearch(event) {
  const platforms = [...document.querySelectorAll('input[name="platform"]:checked')].map(el => el.value);
  if (!platforms.length) return toast("Hãy chọn ít nhất một nền tảng", true);
  const mode = document.getElementById("researchMode").value;
  const body = {
    mode,
    platforms,
    industry: document.getElementById("researchIndustry").value,
    keyword: document.getElementById("researchKeyword").value.trim(),
    sort: document.getElementById("researchSort").value,
    channel_urls: document.getElementById("channelUrls").value.split(/\r?\n/).map(x => x.trim()).filter(Boolean),
    max_videos: 20
  };
  state.domainId = body.industry;
  if (mode === "live" && !body.channel_urls.length) return toast("Chế độ Live cần ít nhất một URL kênh", true);
  await withBusy(event.currentTarget, "Đang research…", async () => {
    const result = await api("/api/research", {method:"POST", body});
    state.rows = result.rows || await pollJob(result.job.id, "researchStatus");
    renderResearchTable();
    setStage("research", "done", "Hoàn thành");
    setStage("select", "active", "Chờ duyệt");
    toast(`Tìm thấy ${state.rows.length} video phù hợp`);
  });
}

function renderResearchTable() {
  const box = document.getElementById("researchResult");
  if (!state.rows.length) { box.className = "empty-result"; box.textContent = "Không có kết quả. Hãy nới từ khóa hoặc thêm URL kênh."; return; }
  box.className = "table-wrap";
  box.innerHTML = `<table><thead><tr><th>Kênh</th><th>Video</th><th>Link gốc</th><th>Xem</th><th>Like</th><th>Bình luận</th><th>Chia sẻ</th><th>Tương tác</th><th>Viral</th><th>Vì sao viral</th><th></th></tr></thead><tbody>${state.rows.map((r, i) => `
    <tr><td><span class="channel ${esc(r.platform)}">${esc(String(r.platform).toUpperCase())}</span><br><small>${esc(r.channel)}</small></td><td><strong>${esc(r.title)}</strong><br><small>${esc(r.industry_label)}</small></td><td>${r.url ? `<a href="${esc(r.url)}" target="_blank" rel="noopener noreferrer">Mở video ↗</a>` : "—"}</td><td>${esc(r.views_text)}</td><td>${esc(r.likes_text)}</td><td>${esc(r.comments_text)}</td><td>${esc(r.shares_text)}</td><td>${esc(r.engagement_pct)}%</td><td><strong>${esc(r.viral_score)}/100</strong></td><td class="analysis-text">${esc(r.viral_reason)}</td><td><button class="mini-btn approve" data-approve-video="${i}">Duyệt</button></td></tr>`).join("")}</tbody></table>`;
  box.querySelectorAll("[data-approve-video]").forEach(button => button.addEventListener("click", () => approveVideo(Number(button.dataset.approveVideo))));
}

async function approveVideo(index) {
  const selected = state.rows[index];
  await withBusy(null, "", async () => {
    const project = await ensureProject(selected.title, selected);
    const mode = document.getElementById("scriptMode")?.value || "demo";
    const result = await api("/api/scripts/generate", {method:"POST", body:{project_id:project.id, selected_video:selected, mode, domain_id:state.domainId}});
    state.scripts = result.scripts || await pollJob(result.job.id, "researchStatus");
    setStage("select", "done", "Đã duyệt");
    setStage("script", "active", "3 phương án");
    toast("Đã duyệt video và tạo ba kịch bản");
    renderDetail("script");
  });
}

function renderScripts(box) {
  const cards = state.scripts.length ? `<div class="script-grid">${state.scripts.map((s, i) => scriptCard(s, i)).join("")}</div>` : `
    <div class="empty-result"><strong>Nhập kịch bản có sẵn</strong><p>Tạo project mới và duyệt trực tiếp, không cần research.</p></div>
    <div class="field-grid" style="margin-top:14px"><label class="field-label">Tên video<input class="field" id="manualTitle" value="Personal Brand Video"></label><label class="field-label">Ngành/ngách<select class="field" id="manualDomain">${selectOptions(domainOptions, state.domainId)}</select></label><label class="field-label">Kịch bản<textarea id="manualScript" style="min-height:170px" placeholder="Dán kịch bản đã có vào đây…"></textarea></label></div>
    <button class="mini-btn primary-action" id="manualApprove" style="margin-top:12px">Duyệt kịch bản nhập sẵn</button>`;
  box.innerHTML = workShell("Thao tác bước 03", "Viết, sửa và duyệt kịch bản", "Chỉ bản được duyệt mới được dùng để tạo video.", cards);
  box.querySelectorAll("[data-approve-script]").forEach(button => button.addEventListener("click", () => approveScript(Number(button.dataset.approveScript), button)));
  document.getElementById("manualApprove")?.addEventListener("click", approveManualScript);
}

function scriptCard(script, index) {
  const analysis = script.analysis || {};
  const claims = (script.claim_check || []).map(item => `<span class="score"><strong>${esc(item.level)}:</strong> ${esc(item.label)}</span>`).join("");
  return `<article class="script-card" id="scriptCard${index}"><h4>Kịch bản ${index + 1} · ${esc(script.angle)}</h4><div class="score-row">${Object.entries(analysis).map(([k,v]) => `<span class="score"><strong>${esc(k)}:</strong> ${esc(v)}</span>`).join("")}${claims}</div><textarea aria-label="Kịch bản ${index + 1}">${esc(script.text)}</textarea><button class="mini-btn approve" style="width:100%;margin-top:9px" data-approve-script="${index}">Duyệt kịch bản ${index + 1}</button></article>`;
}

async function approveScript(index, button) {
  const script = state.scripts[index];
  const text = document.querySelector(`#scriptCard${index} textarea`).value.trim();
  if (!text) return toast("Kịch bản không được để trống", true);
  await withBusy(button, "Đang duyệt…", async () => {
    const result = await api("/api/scripts/approve", {method:"POST", body:{project_id:state.project.id, script_id:script.id, text, approved_at:new Date().toISOString()}});
    state.approvedScript = result.approved;
    document.querySelectorAll(".script-card").forEach(card => card.classList.remove("selected"));
    document.getElementById(`scriptCard${index}`).classList.add("selected");
    setStage("script", "done", "Đã duyệt");
    setStage("heygen", "active", "Chọn route");
    toast("Kịch bản đã được khóa cho bước sản xuất");
    renderDetail("heygen");
  });
}

async function approveManualScript(event) {
  const text = document.getElementById("manualScript").value.trim();
  if (!text) return toast("Hãy dán kịch bản trước", true);
  await withBusy(event.currentTarget, "Đang lưu…", async () => {
    state.domainId = document.getElementById("manualDomain").value;
    const project = await ensureProject(document.getElementById("manualTitle").value.trim() || "Personal Brand Video");
    const result = await api("/api/scripts/approve", {method:"POST", body:{project_id:project.id, script_id:"manual", text, approved_at:new Date().toISOString()}});
    state.approvedScript = result.approved;
    setStage("script", "done", "Đã duyệt");
    renderDetail("heygen");
  });
}

function renderProduction(box) {
  const ready = Boolean(state.project && state.approvedScript);
  box.innerHTML = workShell("Thao tác bước 04", "Chọn luồng tạo video gốc", ready ? "Kịch bản đã duyệt sẵn sàng sản xuất." : "Hãy duyệt kịch bản trước khi tạo video.", `
    <div class="route-tabs"><button class="route-tab active" id="avatarRoute"><strong>01 · HeyGen Avatar</strong><span>Nhiều avatar look trong cùng video.</span></button><button class="route-tab" id="nofaceRoute"><strong>02 · Video No-face</strong><span>Voice + chart + infographic + footage.</span></button></div>
    <div id="heygenPane">
      <div class="field-grid"><label class="field-label">HeyGen API key<input class="field" id="heygenKey" type="password" autocomplete="off" placeholder="Lưu cục bộ trong .env"></label><label class="field-label">Voice ID<input class="field" id="voiceId" placeholder="HeyGen voice_id"></label><label class="field-label">Avatar IDs — ngăn cách bằng dấu phẩy<textarea id="avatarIds" style="min-height:90px" placeholder="avatar_13, avatar_15, avatar_18"></textarea></label><label class="field-label">Tốc độ<input class="field" id="voiceSpeed" type="number" min="0.5" max="1.5" step="0.05" value="1.0"></label></div>
      <div class="metric-strip"><div class="metric"><b id="durationEstimate">0 giây</b><span>Ước tính theo số từ</span></div><div class="metric"><b id="sceneEstimate">0 scene</b><span>Chia theo đoạn</span></div><div class="metric"><b>720×1280</b><span>Video dọc</span></div><div class="metric"><b>Theo tài khoản</b><span>Credit HeyGen</span></div></div>
      <div class="callout">API key chỉ lưu trong file .env ở máy này. Trước lúc gửi render, ứng dụng luôn hỏi xác nhận tiêu credit.</div>
      <div class="toolbar" style="margin-top:14px"><button class="mini-btn" id="saveHeygen">Lưu cấu hình</button><button class="mini-btn primary-action" id="runHeygen" ${ready ? "" : "disabled"}>Kiểm tra & tạo video</button></div><div id="productionStatus" class="status-line"></div>
    </div>
    <div id="nofacePane" class="hidden-pane"><div class="field-grid"><label class="field-label">Nguồn voice<select class="field" id="voiceSource"><option value="tts">AI voice / TTS</option><option value="upload">Voice thu âm</option><option value="text-music">Text + nhạc</option></select></label><label class="field-label">Phong cách<select class="field" id="nofaceStyle">${selectOptions(editStyleOptions, state.styleId)}</select></label></div><div class="visual-mix"><div class="visual-type"><b>Proof chính</b>Theo domain pack đã chọn.</div><div class="visual-type"><b>Tư liệu thật</b>Owned asset, demo hoặc cảnh thật.</div><div class="visual-type"><b>Bối cảnh phụ</b>Stock có license và source.</div></div><button class="mini-btn primary-action" id="runNoface" style="margin-top:14px" ${ready ? "" : "disabled"}>Tạo kế hoạch No-face</button></div>`);
  const text = state.approvedScript?.text || "";
  document.getElementById("durationEstimate").textContent = `${Math.max(1, Math.round(text.split(/\s+/).filter(Boolean).length / 2.7))} giây`;
  document.getElementById("sceneEstimate").textContent = `${makeScenes(text).length} scene`;
  document.getElementById("avatarRoute").addEventListener("click", () => showRoute("avatar"));
  document.getElementById("nofaceRoute").addEventListener("click", () => showRoute("no-face"));
  document.getElementById("saveHeygen").addEventListener("click", saveHeygen);
  document.getElementById("runHeygen").addEventListener("click", runHeygen);
  document.getElementById("runNoface").addEventListener("click", runNoface);
}

function showRoute(route) {
  state.route = route;
  document.getElementById("heygenPane").classList.toggle("hidden-pane", route !== "avatar");
  document.getElementById("nofacePane").classList.toggle("hidden-pane", route !== "no-face");
  document.getElementById("avatarRoute").classList.toggle("active", route === "avatar");
  document.getElementById("nofaceRoute").classList.toggle("active", route === "no-face");
}

function makeScenes(text) {
  const blocks = text.split(/\n\s*\n/).map(x => x.trim()).filter(Boolean);
  return (blocks.length ? blocks : [text]).map((value, index) => ({id:index + 1, text:value}));
}

async function saveHeygen(event) {
  const key = document.getElementById("heygenKey").value.trim();
  await withBusy(event.currentTarget, "Đang lưu…", async () => {
    await api("/api/settings", {method:"POST", body:{secrets:key ? {HEYGEN_API_KEY:key} : {}, settings:{}}});
    document.getElementById("heygenKey").value = "";
    toast("Đã lưu cấu hình HeyGen cục bộ");
  });
}

async function runHeygen(event) {
  const voiceId = document.getElementById("voiceId").value.trim();
  const avatarIds = document.getElementById("avatarIds").value.split(/[\n,]+/).map(x => x.trim()).filter(Boolean);
  if (!voiceId || !avatarIds.length) return toast("Cần Voice ID và ít nhất một Avatar ID", true);
  if (!window.confirm("Gửi render HeyGen có thể tiêu credit trong tài khoản. Bạn xác nhận tiếp tục?")) return;
  await withBusy(event.currentTarget, "HeyGen đang render…", async () => {
    const result = await api("/api/heygen", {method:"POST", body:{project_id:state.project.id, voice_id:voiceId, avatar_ids:avatarIds, speed:Number(document.getElementById("voiceSpeed").value), scenes:makeScenes(state.approvedScript.text), confirmed:true}});
    const output = await pollJob(result.job.id, "productionStatus");
    setStage("heygen", "done", "Video sẵn sàng");
    toast(`Đã tải ${output.file}`);
    renderDetail("edit");
  });
}

async function runNoface(event) {
  await withBusy(event.currentTarget, "Đang tạo kế hoạch…", async () => {
    state.styleId = document.getElementById("nofaceStyle").value;
    await api("/api/noface", {method:"POST", body:{project_id:state.project.id, voice_source:document.getElementById("voiceSource").value, style:document.getElementById("nofaceStyle").value, target_seconds:55, scenes:makeScenes(state.approvedScript.text)}});
    state.route = "no-face";
    setStage("heygen", "done", "No-face plan");
    toast("Đã tạo noface_plan.json; sẵn sàng chuyển sang edit");
    renderDetail("edit");
  });
}

function renderUpload(box) {
  box.innerHTML = workShell("Thao tác bước 05", "Tải video gốc có sẵn", "Dùng cho edit-only hoặc thay nguồn HeyGen/no-face.", `<div class="field-grid"><label class="field-label">Tên project<input class="field" id="uploadTitle" value="Video edit-only"></label><label class="field-label">Chọn file video<input class="field" id="sourceFile" type="file" accept="video/*,audio/*"></label></div><button class="mini-btn primary-action" id="uploadSource" style="margin-top:14px">Tải lên project</button><div id="uploadStatus" class="status-line"></div>`);
  document.getElementById("uploadSource").addEventListener("click", uploadSource);
}

async function uploadSource(event) {
  const file = document.getElementById("sourceFile").files[0];
  if (!file) return toast("Hãy chọn video hoặc audio", true);
  await withBusy(event.currentTarget, "Đang tải lên…", async () => {
    const project = await ensureProject(document.getElementById("uploadTitle").value.trim() || file.name);
    const result = await api("/api/upload", {method:"POST", headers:{"Content-Type":file.type || "application/octet-stream", "X-Project-ID":project.id, "X-Filename":encodeURIComponent(file.name), "X-Upload-Kind":"source"}, body:file});
    state.route = "source-video";
    setStage("align", "done", "Đã nhận file");
    document.getElementById("uploadStatus").textContent = `${result.file} · ${Math.round(result.size / 1024 / 1024 * 10) / 10} MB`;
    toast("Đã lưu video gốc vào project");
  });
}

function renderEdit(box) {
  const versions = state.project?.versions || [];
  const finalFile = state.media.find(name => /^final.*\.mp4$/i.test(name));
  const finalUrl = finalFile && state.project ? `/api/media?project_id=${encodeURIComponent(state.project.id)}&file=${encodeURIComponent(finalFile)}` : "";
  const preview = finalUrl ? `<video controls preload="metadata" style="width:100%;max-height:560px;border-radius:14px" src="${finalUrl}"></video>` : `<div class="video-frame"><div style="text-align:center"><div class="play">▶</div><p>Preview xuất hiện khi project có final.mp4</p></div></div>`;
  box.innerHTML = workShell("Thao tác bước 08", "Edit đa phong cách", "Tạo phiếu edit và beat-level edit plan, sau đó gửi feedback theo từng vòng; không ghi đè bản đã duyệt.", `
    <label class="field-label">Phong cách edit<select class="field" id="editStyle">${selectOptions(editStyleOptions, state.styleId)}</select></label>
    <div class="video-review"><div>${preview}<div class="toolbar" style="margin-top:12px"><a class="mini-btn download" id="downloadFinal" href="${finalUrl || "#"}" ${finalUrl ? "download" : 'aria-disabled="true"'}>Tải ${esc(finalFile || "final.mp4")}</a><button class="mini-btn primary-action" id="createEdit">Tạo phiếu edit</button></div></div><div><label class="field-label">Yêu cầu chỉnh sửa<textarea id="editFeedback" style="min-height:150px" placeholder="00:12 tăng cỡ chữ; 00:27 đổi chart; giảm nhạc nền…"></textarea></label><button class="mini-btn approve" id="sendFeedback" style="width:100%;margin-top:10px">Lưu feedback vòng mới</button><div id="editStatus" class="status-line"></div></div></div>
    <div class="block"><h4>Lịch sử feedback</h4><div class="version-list">${versions.length ? versions.map(v => `<div class="version"><strong>V${esc(v.version)}</strong><span>${esc(v.text)}</span><small>${esc(v.created_at || "")}</small></div>`).join("") : `<div class="feedback-item">Chưa có feedback.</div>`}</div></div>`);
  document.getElementById("downloadFinal").addEventListener("click", event => { if (!finalUrl) { event.preventDefault(); toast("Project chưa có bản final để tải", true); } });
  document.getElementById("createEdit").addEventListener("click", createEditRequest);
  document.getElementById("sendFeedback").addEventListener("click", sendFeedback);
}

async function createEditRequest(event) {
  if (!state.project) return toast("Hãy tạo project hoặc upload video trước", true);
  await withBusy(event.currentTarget, "Đang tạo phiếu…", async () => {
    state.styleId = document.getElementById("editStyle").value;
    await api("/api/edit-request", {method:"POST", body:{project_id:state.project.id, route:state.route, style_id:state.styleId, feedback:document.getElementById("editFeedback").value.trim()}});
    setStage("edit", "active", "Đã tạo phiếu");
    document.getElementById("editStatus").textContent = "Đã tạo EDIT_REQUEST.md, edit_request.json và beat-level edit_plan.json.";
    toast("Phiếu edit đã sẵn sàng cho skill multi-style-video-editor");
  });
}

function renderQa(box) {
  const checks = [["full_watch","Đã xem toàn bộ video"],["caption_safe_area","Caption nằm trong vùng an toàn"],["voice_alignment","Visual/caption bám đúng voice"],["no_flash_frames","Không có flash frame"],["source_traceability","Tư liệu và số liệu truy vết được nguồn"],["claims_checked","Claim đúng domain pack"]];
  box.innerHTML = workShell("Thao tác bước 09", "QA và duyệt final", "Chỉ duyệt khi đã kiểm tra đủ sáu điều kiện.", `<div class="block">${checks.map(([id,label]) => `<label class="choice"><input type="checkbox" name="qaCheck" value="${id}"> ${label}</label>`).join("")}</div><label class="field-label">Ghi chú reviewer<textarea id="qaNote" placeholder="Ghi chú lỗi hoặc lý do duyệt…"></textarea></label><button class="mini-btn approve" id="approveQa">Lưu QA & duyệt final</button><div id="qaStatus" class="status-line"></div>`);
  document.getElementById("approveQa").addEventListener("click", async event => {
    if (!state.project) return toast("Chưa có project", true);
    const checked = [...document.querySelectorAll('input[name="qaCheck"]:checked')].map(item => item.value);
    const checksPayload = Object.fromEntries(checks.map(([id]) => [id, checked.includes(id)]));
    await withBusy(event.currentTarget, "Đang lưu QA…", async () => {
      const result = await api("/api/qa", {method:"POST", body:{project_id:state.project.id, checks:checksPayload, approved:checked.length === checks.length, reviewer_note:document.getElementById("qaNote").value.trim()}});
      document.getElementById("qaStatus").textContent = result.report.approved ? "Final đã được duyệt." : "QA chưa đủ; chưa duyệt final.";
      setStage("qa", result.report.approved ? "done" : "active", result.report.approved ? "Đã duyệt" : "Chưa đạt");
    });
  });
}

async function sendFeedback(event) {
  if (!state.project) return toast("Chưa có project", true);
  const text = document.getElementById("editFeedback").value.trim();
  if (!text) return toast("Hãy nhập chi tiết cần sửa", true);
  await withBusy(event.currentTarget, "Đang lưu…", async () => {
    const data = await api("/api/feedback", {method:"POST", body:{project_id:state.project.id, text, created_at:new Date().toISOString()}});
    state.project.versions = data.versions;
    toast("Đã lưu feedback; không ghi đè phiên bản cũ");
    renderEdit(document.getElementById("workbench"));
  });
}

function renderPublish(box) {
  box.innerHTML = workShell("Thao tác bước 11", "Đăng bài hoặc bỏ qua", "Skip không tạo thay đổi bên ngoài. Đăng thật yêu cầu xác nhận lại ngay tại thời điểm chạy.", `
    <div class="toolbar"><label class="choice"><input type="checkbox" name="publishPlatform" checked value="facebook"> Facebook</label><label class="choice"><input type="checkbox" name="publishPlatform" checked value="youtube"> YouTube</label><label class="choice"><input type="checkbox" name="publishPlatform" value="tiktok"> TikTok</label></div>
    <div class="field-grid"><label class="field-label">Chế độ<select class="field" id="publishAction"><option value="schedule">Hẹn lịch</option><option value="now">Đăng ngay</option></select></label><label class="field-label">Thời gian — YYYY-MM-DD HH:MM<input class="field mono" id="publishSchedule" placeholder="2026-09-15 20:10"></label><label class="field-label">Profile<input class="field" id="publishProfile" value="cong"></label><label class="field-label">Tên file video<input class="field" id="publishVideo" value="final.mp4"></label></div>
    <div class="callout">YouTube dùng publisher Playwright theo project; TikTok có thể cần chuyển sang package đăng thủ công nếu API chưa được duyệt.</div>
    <div class="toolbar" style="margin-top:14px"><button class="mini-btn skip" id="skipPublish">Bỏ qua đăng bài</button><button class="mini-btn primary-action" id="runPublish">Xác nhận & chạy</button></div><div id="publishJob" class="status-line"></div>`);
  document.getElementById("skipPublish").addEventListener("click", skipPublish);
  document.getElementById("runPublish").addEventListener("click", publishNow);
}

async function skipPublish(event) {
  await withBusy(event.currentTarget, "Đang lưu…", async () => {
    const project = await ensureProject("Publish package");
    const data = await api("/api/publish", {method:"POST", body:{project_id:project.id, mode:"skip"}});
    updateProject(data.project);
    setStage("publish", "done", "SKIP");
    document.getElementById("publishLabel").textContent = "Đã bỏ qua xuất bản";
    toast("Đã hoàn tất tại file; không đăng ra ngoài");
  });
}

async function publishNow(event) {
  if (!state.project) return toast("Hãy tạo project và có final.mp4 trước", true);
  const platforms = [...document.querySelectorAll('input[name="publishPlatform"]:checked')].map(el => el.value);
  if (!platforms.length) return toast("Hãy chọn nền tảng", true);
  if (!window.confirm(`Chuẩn bị tạo thay đổi thật trên: ${platforms.join(", ")}. Tiếp tục?`)) return;
  await withBusy(event.currentTarget, "Đang xuất bản…", async () => {
    const action = document.getElementById("publishAction").value;
    const result = await api("/api/publish", {method:"POST", body:{project_id:state.project.id, mode:action, platforms, schedule:action === "schedule" ? document.getElementById("publishSchedule").value.trim() : "", profile:document.getElementById("publishProfile").value.trim(), video:document.getElementById("publishVideo").value.trim(), confirmed:true}});
    await pollJob(result.job.id, "publishJob");
    setStage("publish", "done", "Hoàn thành");
    toast("Publisher đã chạy; xem publish.json để kiểm tra kết quả");
  });
}

function applyMode(mode) {
  currentMode = mode;
  setView("workflow");
  document.querySelectorAll("[data-modes]").forEach(el => el.classList.toggle("hidden", !el.dataset.modes.split(" ").includes(mode)));
  document.querySelectorAll(".mode").forEach(el => el.classList.toggle("active", el.dataset.mode === mode));
  const names = {full:"Research → Video → Phân phối", script:"Kịch bản → Video → Phân phối", edit:"Video gốc → Editorial Edit", publish:"Final.mp4 → Phân phối"};
  document.getElementById("flowTitle").textContent = names[mode];
  renderDetail(modes[mode][0]);
}

async function init() {
  try {
    await api("/api/health", {headers:{}});
    document.getElementById("backendStatus").innerHTML = '<i class="pulse"></i>Localhost đang chạy';
    const listing = await api("/api/projects", {headers:{}});
    if (listing.projects?.length) {
      const resumed = await api(`/api/projects/${encodeURIComponent(listing.projects[0].id)}`, {headers:{}});
      updateProject(resumed.project);
      state.domainId = resumed.project.domain_id || "finance";
      state.styleId = resumed.project.style_id || "editorial-proof";
      state.scripts = resumed.artifacts.script_candidates || [];
      state.approvedScript = resumed.artifacts.approved_script || null;
      state.route = resumed.artifacts.noface_plan ? "no-face" : (resumed.project.route || "avatar");
      state.media = resumed.artifacts.media || [];
      state.project.versions = resumed.artifacts.edit_feedback || resumed.project.versions || [];
      toast(`Đã phục hồi project ${resumed.project.id}`);
    }
  } catch (error) {
    document.getElementById("backendStatus").textContent = "Backend chưa kết nối";
    toast("Không kết nối được localhost backend", true);
  }
  renderWorkbench("research");
  setView(location.hash === "#map" ? "map" : "workflow", false);
}

function resetProject() {
  state.project = null;
  state.rows = [];
  state.scripts = [];
  state.approvedScript = null;
  state.media = [];
  updateProject(null);
  stageEls.forEach(el => {
    el.dataset.state = "";
    el.querySelector(".status").textContent = el.dataset.gate === "true" ? "Cần duyệt" : "Tự động";
  });
  applyMode(currentMode);
  toast("Đã bắt đầu project mới");
}

document.querySelectorAll(".view-tab").forEach(button => button.addEventListener("click", () => setView(button.dataset.view)));
window.addEventListener("hashchange", () => setView(location.hash === "#map" ? "map" : "workflow", false));
document.querySelectorAll(".mode").forEach(button => button.addEventListener("click", () => applyMode(button.dataset.mode)));
stageEls.forEach(button => button.addEventListener("click", () => renderDetail(button.dataset.step)));
document.querySelectorAll(".switch").forEach(button => button.addEventListener("click", () => button.classList.toggle("on")));
document.getElementById("runBtn").addEventListener("click", () => renderDetail(modes[currentMode].find(key => stageEls.find(el => el.dataset.step === key)?.dataset.state !== "done") || modes[currentMode][0]));
document.getElementById("resetBtn").addEventListener("click", resetProject);
document.getElementById("workflowResetBtn").addEventListener("click", resetProject);
document.getElementById("publishMode").addEventListener("change", event => { if (event.target.value === "skip") document.getElementById("publishStatus").textContent = "SKIP"; renderDetail("publish"); });
init();
