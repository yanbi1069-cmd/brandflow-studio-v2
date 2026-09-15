"use client";

import { useEffect, useMemo, useState } from "react";
import domainPacks from "@/config/domain-packs.json";
import contentFormats from "@/config/content-formats.json";
import editStyles from "@/config/edit-styles-v2.json";
import styles from "./finance-workflow.module.css";

const STORAGE_KEY = "personal-brand-video-agent-v3-finance-core";
const QA_DEFAULT = { fullWatch: false, noFlash: false, captions: false, proof: false, audio: false, exportSpec: false };
const PLATFORM_LABELS = { youtube: "YouTube", tiktok: "TikTok", facebook: "Facebook" };
const API_GUIDES = [
  { id: "apify", name: "Apify", purpose: "Thu thập dữ liệu và chỉ số video", home: "https://apify.com/", keyUrl: "https://console.apify.com/account/integrations", steps: ["Đăng ký hoặc đăng nhập Apify.", "Mở Settings → API & Integrations.", "Tạo token riêng cho BrandFlow, giới hạn quyền nếu có thể.", "Sao chép token và dán vào mục Cài đặt."] },
  { id: "kyma", name: "Kyma API", purpose: "Phân tích nội dung và viết kịch bản", home: "https://kymaapi.com/", keyUrl: "https://kymaapi.com/signup", steps: ["Tạo tài khoản Kyma API.", "Đăng nhập trang quản lý API key.", "Tạo key dành riêng cho BrandFlow.", "Sao chép key và dán vào mục Cài đặt."] },
  { id: "heygen", name: "HeyGen", purpose: "Tạo video AI Avatar", home: "https://www.heygen.com/", keyUrl: "https://app.heygen.com/settings?nav=API", steps: ["Đăng nhập HeyGen.", "Mở Settings → API.", "Tạo hoặc tạo lại API token.", "Dán token vào Cài đặt; mỗi lần render trả phí vẫn cần xác nhận."] },
  { id: "pexels", name: "Pexels", purpose: "Nguồn B-roll đời sống ưu tiên", home: "https://www.pexels.com/", keyUrl: "https://www.pexels.com/api/new/", steps: ["Tạo tài khoản Pexels.", "Mở trang Pexels API.", "Yêu cầu API key.", "Dán key vào Cài đặt; BrandFlow sẽ lưu link nguồn và tác giả trong media manifest."] },
  { id: "pixabay", name: "Pixabay", purpose: "Nguồn B-roll dự phòng khi Pexels không phù hợp", home: "https://pixabay.com/", keyUrl: "https://pixabay.com/api/docs/", steps: ["Tạo hoặc đăng nhập tài khoản Pixabay.", "Mở Pixabay API Documentation để xem API key của tài khoản.", "Sao chép key và dán vào mục Cài đặt.", "BrandFlow tải clip về job, cache kết quả và lưu trang nguồn/tác giả theo Content License."] },
];
const DEFAULT_TEXT_OVERLAY = {
  enabled: true,
  preset: "finance-editorial",
  kicker: "ĐIỂM CẦN NHỚ",
  lines: "",
  fontSize: 62,
  position: "top",
  align: "left",
  maxCharsPerLine: 24,
  textColor: "#F4F7EF",
  accentColor: "#B6FF36",
  backgroundColor: "#060B16",
  backgroundOpacity: 0.72,
  accentStripe: false,
  uppercase: true,
};

function Icon({ name }) {
  const paths = {
    check: <path d="m5 12 4 4L19 6" />,
    search: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
    download: <><path d="M12 3v12m0 0 4-4m-4 4-4-4"/><path d="M5 20h14"/></>,
    arrow: <path d="m9 18 6-6-6-6"/>,
    shield: <><path d="M12 3 5 6v5c0 4.5 2.8 7.7 7 10 4.2-2.3 7-5.5 7-10V6l-7-3Z"/><path d="m9 12 2 2 4-5"/></>,
    gear: <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-2.83 2.83-.06-.06a1.7 1.7 0 0 0-1.88-.34 1.7 1.7 0 0 0-1.03 1.56V21h-4v-.08A1.7 1.7 0 0 0 8.97 19.4a1.7 1.7 0 0 0-1.88.34l-.06.06-2.83-2.83.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-1.52-1H3v-4h.08A1.7 1.7 0 0 0 4.6 9a1.7 1.7 0 0 0-.34-1.88l-.06-.06 2.83-2.83.06.06A1.7 1.7 0 0 0 8.97 4.6 1.7 1.7 0 0 0 10 3.08V3h4v.08A1.7 1.7 0 0 0 15.03 4.6a1.7 1.7 0 0 0 1.88-.34l.06-.06 2.83 2.83-.06.06A1.7 1.7 0 0 0 19.4 9c.17.62.75 1 1.52 1H21v4h-.08c-.77 0-1.35.38-1.52 1Z"/></>,
    book: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H11v16H6.5A2.5 2.5 0 0 0 4 21.5Z"/><path d="M20 5.5A2.5 2.5 0 0 0 17.5 3H13v16h4.5a2.5 2.5 0 0 1 2.5 2.5Z"/></>,
  };
  return <svg viewBox="0 0 24 24" aria-hidden="true">{paths[name] || paths.check}</svg>;
}

function downloadFile(name, value, type = "application/json") {
  const body = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  const url = URL.createObjectURL(new Blob([body], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  URL.revokeObjectURL(url);
}

function Field({ label, help, children }) {
  return <label className={styles.field}><span>{label}</span>{children}{help && <small>{help}</small>}</label>;
}

function Section({ number, title, subtitle, state, children }) {
  return <section className={styles.section}>
    <header className={styles.sectionHead}><b>{number}</b><div><h2>{title}</h2><p>{subtitle}</p></div>{state && <span className={styles.state}><Icon name="check" />{state}</span>}</header>
    {children}
  </section>;
}

function Status({ children, tone = "info" }) {
  return <div className={`${styles.status} ${styles[tone]}`} role="status">{children}</div>;
}

function initialBrand(domain) {
  return { name: "Thương hiệu của bạn", niche: domain.niche, audience: domain.audience, voice: domain.voice, cta: "Theo dõi kênh để xem thêm nội dung thực hành." };
}

function researchRow(row) {
  return {
    ...row,
    id: row.id,
    viewsText: row.views_text ?? row.viewsText ?? "—",
    likesText: row.likes_text ?? row.likesText ?? "—",
    commentsText: row.comments_text ?? row.commentsText ?? "—",
    sharesText: row.shares_text ?? row.sharesText ?? "—",
    engagementPct: row.engagement_pct ?? row.engagementPct ?? null,
    viralReason: row.viral_reason ?? row.viralReason ?? "Nội dung có hiệu suất nổi bật trong nhóm video được quét.",
  };
}

function elapsedLabel(total) {
  const minutes = Math.floor(total / 60);
  const seconds = total % 60;
  return minutes ? `${minutes} phút ${seconds.toString().padStart(2, "0")} giây` : `${seconds} giây`;
}

function validScriptCandidate(item) {
  const useful = (value, minimum) => String(value || "").trim().length >= minimum && !/^[\s.…·_-]+$/.test(String(value || ""));
  return useful(item?.angle, 4) && useful(item?.hook, 12) && useful(item?.body, 120) && useful(item?.cta, 8);
}

function overlaySuggestions(script) {
  if (!script) return "";
  const sentences = [script.hook, ...String(script.body || "").split(/(?<=[.!?])\s+|\r?\n/), script.cta]
    .map((value) => String(value || "").trim())
    .filter(Boolean)
    .map((value) => value.split(/\s+/).slice(0, 10).join(" "));
  return [...new Set(sentences)].slice(0, 6).join("\n");
}

export default function FinanceWorkflow() {
  const [hydrated, setHydrated] = useState(false);
  const entryMode = "full";
  const [domainId, setDomainId] = useState("finance");
  const [formatId, setFormatId] = useState("evidence-explainer");
  const domain = useMemo(() => domainPacks.find((item) => item.id === domainId) || domainPacks[0], [domainId]);
  const format = useMemo(() => contentFormats.find((item) => item.id === formatId) || contentFormats[0], [formatId]);
  const [brand, setBrand] = useState(() => initialBrand(domainPacks.find((item) => item.id === "finance") || domainPacks[0]));
  const [research, setResearch] = useState({ mode: "topic", platforms: ["youtube", "tiktok", "facebook"], keyword: "", channelUrls: "", language: "vi", period: "12m" });
  const [rows, setRows] = useState([]);
  const [researchMode, setResearchMode] = useState("demo");
  const [manualTopic, setManualTopic] = useState("");
  const [selectedVideos, setSelectedVideos] = useState([]);
  const [researchApproved, setResearchApproved] = useState(false);
  const [scripts, setScripts] = useState([]);
  const [selectedScriptId, setSelectedScriptId] = useState("");
  const [scriptMode, setScriptMode] = useState("write");
  const [scriptSourceId, setScriptSourceId] = useState("");
  const [importedScript, setImportedScript] = useState("");
  const selectableScript = (item) => item?.sourceId === "imported" || validScriptCandidate(item);
  const selectedScript = scripts.find((item) => item.id === selectedScriptId && selectableScript(item)) || scripts.find(selectableScript) || null;
  const [scriptApproved, setScriptApproved] = useState(false);
  const [sourceRoute, setSourceRoute] = useState("avatar");
  const [avatar, setAvatar] = useState({ voiceId: "", avatarIds: "", speed: 1, duration: 55, test: true, costConfirmed: false, notify: true });
  const [noface, setNoface] = useState({ voiceSource: "tts", visualMix: "50 / 30 / 20" });
  const [voiceUpload, setVoiceUpload] = useState(null);
  const [upload, setUpload] = useState(null);
  const [sourceFile, setSourceFile] = useState(null);
  const [videoPreviewUrl, setVideoPreviewUrl] = useState("");
  const [previewKind, setPreviewKind] = useState("");
  const [finalVideoName, setFinalVideoName] = useState("");
  const [sourceArtifact, setSourceArtifact] = useState(null);
  const [styleId, setStyleId] = useState("editorial-proof");
  const selectedStyle = editStyles.find((item) => item.id === styleId) || editStyles[0];
  const [textOverlay, setTextOverlay] = useState(DEFAULT_TEXT_OVERLAY);
  const [editPlan, setEditPlan] = useState(null);
  const [feedbackText, setFeedbackText] = useState("");
  const [feedback, setFeedback] = useState([]);
  const [videoTask, setVideoTask] = useState("");
  const [taskMessage, setTaskMessage] = useState("");
  const [taskStartedAt, setTaskStartedAt] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [heygenComplete, setHeygenComplete] = useState(false);
  const [qa, setQa] = useState(QA_DEFAULT);
  const [finalApproved, setFinalApproved] = useState(false);
  const [publish, setPublish] = useState({ mode: "skip", platforms: [], profile: "", schedule: "", confirmed: false });
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState("");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [guideOpen, setGuideOpen] = useState(false);
  const [secrets, setSecrets] = useState({ apify: "", kyma: "", heygen: "", pexels: "", pixabay: "" });
  const [localAgent, setLocalAgent] = useState({ checked: false, online: false, heygen: false, defaults: {} });

  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
      if (saved) {
        if (saved.domainId) setDomainId(saved.domainId);
        if (saved.formatId) setFormatId(saved.formatId);
        if (saved.brand) setBrand(saved.brand);
        if (saved.research) setResearch((current) => ({ ...current, ...saved.research }));
        if (saved.rows) setRows(saved.rows);
        if (saved.manualTopic) setManualTopic(saved.manualTopic);
        if (saved.selectedVideos) setSelectedVideos(saved.selectedVideos);
        else if (saved.selectedVideo) setSelectedVideos([saved.selectedVideo]);
        if (saved.researchApproved) setResearchApproved(saved.researchApproved);
        if (saved.scripts) setScripts(saved.scripts);
        if (saved.selectedScriptId) setSelectedScriptId(saved.selectedScriptId);
        if (saved.scriptApproved) setScriptApproved(saved.scriptApproved);
        if (saved.sourceRoute) setSourceRoute(saved.sourceRoute);
        if (saved.avatar) setAvatar((current) => ({ ...current, ...saved.avatar }));
        if (saved.noface) setNoface(saved.noface);
        if (saved.upload) setUpload(saved.upload);
        if (saved.sourceArtifact) setSourceArtifact(saved.sourceArtifact);
        if (saved.styleId) setStyleId(saved.styleId);
        if (saved.textOverlay) setTextOverlay((current) => ({ ...current, ...saved.textOverlay }));
        if (saved.editPlan) setEditPlan(saved.editPlan);
        if (saved.feedback) setFeedback(saved.feedback);
        if (saved.qa) setQa(saved.qa);
        if (saved.finalApproved) setFinalApproved(saved.finalApproved);
        if (saved.publish) setPublish(saved.publish);
      }
    } catch {} finally { setHydrated(true); }
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ domainId, formatId, brand, research, rows, manualTopic, selectedVideos, researchApproved, scripts, selectedScriptId, scriptApproved, sourceRoute, avatar, noface, upload, sourceArtifact, styleId, textOverlay, editPlan, feedback, qa, finalApproved, publish }));
  }, [hydrated, domainId, formatId, brand, research, rows, manualTopic, selectedVideos, researchApproved, scripts, selectedScriptId, scriptApproved, sourceRoute, avatar, noface, upload, sourceArtifact, styleId, textOverlay, editPlan, feedback, qa, finalApproved, publish]);

  useEffect(() => {
    if (!hydrated) return;
    fetch("/api/local-agent/health", { cache: "no-store" })
      .then(async (response) => ({ ok: response.ok, data: await response.json() }))
      .then(({ ok, data }) => setLocalAgent({ checked: true, online: ok && data.ok, heygen: Boolean(data.connections?.heygen), defaults: data.defaults || {} }))
      .catch(() => setLocalAgent({ checked: true, online: false, heygen: false, defaults: {} }));
  }, [hydrated]);

  useEffect(() => {
    if (!taskStartedAt) { setElapsedSeconds(0); return; }
    const update = () => setElapsedSeconds(Math.max(0, Math.floor((Date.now() - taskStartedAt) / 1000)));
    update();
    const timer = window.setInterval(update, 1000);
    return () => window.clearInterval(timer);
  }, [taskStartedAt]);

  function chooseDomain(id) {
    const next = domainPacks.find((item) => item.id === id) || domainPacks[0];
    setDomainId(id);
    setBrand((current) => ({ ...current, niche: next.niche, audience: next.audience, voice: next.voice }));
    setStyleId(next.defaultStyle);
    setRows([]); setSelectedVideos([]); setResearchApproved(false); setScripts([]); setScriptApproved(false); setEditPlan(null); setFinalApproved(false);
  }

  function toggleVideo(row) {
    setSelectedVideos((current) => current.some((item) => item.id === row.id) ? current.filter((item) => item.id !== row.id) : [...current, row]);
    setResearchApproved(false);
  }

  function togglePlatform(platform) {
    setResearch((current) => ({ ...current, platforms: current.platforms.includes(platform) ? current.platforms.filter((item) => item !== platform) : [...current.platforms, platform] }));
  }

  async function waitForAgentJob(jobId, fallbackMessage) {
    for (let attempt = 0; attempt < 1200; attempt += 1) {
      const response = await fetch(`/api/local-agent/jobs/${jobId}`, { cache: "no-store" });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Không đọc được trạng thái tác vụ.");
      const job = data.job;
      setTaskMessage(job.message || fallbackMessage);
      if (job.status === "done") return job.result;
      if (["error", "interrupted"].includes(job.status)) throw new Error(job.message || "Tác vụ thất bại.");
      await new Promise((resolve) => setTimeout(resolve, 2500));
    }
    throw new Error("Tác vụ vẫn đang chạy quá thời gian theo dõi; dữ liệu job vẫn được giữ trong local-agent.");
  }

  async function runResearch() {
    const channelUrls = research.channelUrls.split(/\r?\n/).map((value) => value.trim()).filter(Boolean);
    if (research.mode === "topic" && !research.platforms.length) return setNotice("Hãy chọn ít nhất một nền tảng.");
    if (research.mode === "topic" && (!research.keyword.trim() || !brand.niche.trim())) return setNotice("Hãy nhập đầy đủ từ khóa và ngành/ngách.");
    if (research.mode === "channel" && !channelUrls.length) return setNotice("Hãy dán ít nhất một link kênh đối thủ.");
    setBusy("research"); setNotice(""); setTaskStartedAt(Date.now()); setTaskMessage("Đang gửi yêu cầu nghiên cứu tới local-agent...");
    try {
      const response = await fetch("/api/local-agent/research", { method: "POST", headers: { "Content-Type": "application/json", ...(secrets.apify ? { "x-apify-token": secrets.apify } : {}), ...(secrets.kyma ? { "x-kyma-key": secrets.kyma } : {}) }, body: JSON.stringify({ research_mode: research.mode, industry: brand.niche, keyword: research.keyword, platforms: research.platforms, channel_urls: channelUrls, language: research.language, period: research.period, max_videos: 20 }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      const result = await waitForAgentJob(data.job.id, "Agent đang nghiên cứu nội dung...");
      const items = (result.items || []).map(researchRow);
      setRows(items); setResearchMode(result.mode || "live"); setSelectedVideos([]); setResearchApproved(false); setScripts([]); setScriptApproved(false); setEditPlan(null);
      const models = result.models ? ` · Kyma: ${Object.values(result.models).filter((value) => value && value !== "not-needed").join(" → ")}` : "";
      setNotice(`${items.length} video sát yêu cầu từ ${result.candidate_count || items.length} ứng viên${models}${result.warning ? ` · ${result.warning}` : ""}`);
    } catch (error) { setNotice(error.message || "Không thể research."); }
    finally { setBusy(""); setTaskStartedAt(0); setTaskMessage(""); }
  }

  async function generateScripts(sourceVideo) {
    if (!sourceVideo || !researchApproved) return setNotice("Hãy chọn video và đưa vào danh sách viết kịch bản trước.");
    setBusy("script"); setNotice("");
    try {
      const source = sourceVideo;
      const response = await fetch("/api/multi-niche/script", { method: "POST", headers: { "Content-Type": "application/json", ...(secrets.kyma ? { "x-kyma-key": secrets.kyma } : {}) }, body: JSON.stringify({ domainId, formatId, brandName: brand.name, niche: brand.niche, audience: brand.audience, voice: brand.voice, cta: brand.cta, trendTitle: source.title, trendHook: source.viralReason, trendUrl: source.url, targetSeconds: Number(avatar.duration || 55) }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      const candidates = (data.candidates || []).map((item) => ({ ...item, id: `${source.id}-${item.id}`, sourceId: source.id, sourceTitle: source.title }));
      setScripts((current) => [...current.filter((item) => item.sourceId !== source.id), ...candidates]); setSelectedScriptId(candidates[0]?.id || ""); setScriptSourceId(source.id); setScriptApproved(false); setEditPlan(null);
      setNotice(`Đã tạo đúng 3 kịch bản · ${data.sourceMode === "live" ? data.model : "demo không tốn credit"}.`);
    } catch (error) { setScripts((current)=>current.filter((item)=>item.sourceId!==sourceVideo.id)); setNotice(error.message || "Không thể tạo kịch bản."); }
    finally { setBusy(""); }
  }

  function useImportedScript() {
    const text = importedScript.trim();
    if (!text) return setNotice("Hãy nhập nội dung kịch bản có sẵn.");
    const firstLine = text.split(/\r?\n/).find(Boolean) || text;
    const item = { id: `imported-${Date.now()}`, sourceId: "imported", sourceTitle: "Kịch bản nhập sẵn", angle: "Kịch bản của bạn", hook: firstLine, body: text, cta: brand.cta, text, analysis: { origin: "Nội dung do người dùng cung cấp" }, claimCheck: [] };
    setScripts((current) => [...current.filter((script) => script.sourceId !== "imported"), item]);
    setSelectedScriptId(item.id); setScriptSourceId("imported"); setScriptApproved(false); setEditPlan(null);
    setNotice("Đã thêm kịch bản có sẵn. Bạn có thể chỉnh sửa và duyệt trước khi tạo video.");
  }

  function updateScript(field, value) {
    setScripts((current) => current.map((item) => item.id === selectedScript.id ? { ...item, [field]: value, text: [field === "hook" ? value : item.hook, field === "body" ? value : item.body, field === "cta" ? value : item.cta, item.disclaimer].filter(Boolean).join("\n\n") } : item));
    setScriptApproved(false); setEditPlan(null); setFinalApproved(false);
  }

  async function waitForHeyGen(jobId, projectId) {
    const result = await waitForAgentJob(jobId, "HeyGen đang render; vui lòng chờ...");
    const file = result?.file || "heygen_source.mp4";
    const mediaUrl = `/api/local-agent/media?projectId=${encodeURIComponent(projectId)}&file=${encodeURIComponent(file)}`;
    setVideoPreviewUrl(mediaUrl);
    setPreviewKind("source");
    setFinalVideoName(file);
    setSourceArtifact({ type: "heygen_source.mp4", sourceFile: file, route: "avatar", projectId, jobId, status: "ready", result, mediaUrl });
    setHeygenComplete(true);
    setNotice("Video HeyGen đã hoàn thành. Hãy kiểm tra nhanh video nguồn, sau đó chuyển sang bước Dựng video.");
    if (avatar.notify && typeof Notification !== "undefined" && Notification.permission === "granted") new Notification("Video HeyGen đã hoàn thành", { body: "Hãy kiểm tra video nguồn, sau đó chuyển sang bước Dựng video." });
  }

  async function uploadToLocalAgent(file, kind = "source") {
    const response = await fetch("/api/local-agent/upload", { method: "POST", headers: { "Content-Type": file.type || "application/octet-stream", "X-Filename": encodeURIComponent(file.name), "X-Title": encodeURIComponent(selectedScript?.hook || file.name), "X-Domain-ID": domainId, "X-Style-ID": styleId, "X-Upload-Kind": kind }, body: file });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Không thể tải file vào local-agent.");
    if (selectedScript) {
      const approved = await fetch("/api/local-agent/approve-script", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ projectId: data.projectId, script: selectedScript }) });
      const approvalData = await approved.json();
      if (!approved.ok) throw new Error(approvalData.error || "Không thể chuyển kịch bản đã duyệt vào local-agent.");
    }
    return data;
  }

  async function createSourceArtifact() {
    const sourceOnlyMode = entryMode === "edit" || entryMode === "publish";
    if (!scriptApproved && !sourceOnlyMode) return setNotice("Hãy duyệt kịch bản trước khi chuẩn bị source video.");
    if (sourceOnlyMode && sourceRoute !== "upload") return setNotice("Edit-only/Publish-only cần chọn file nguồn.");
    if (sourceRoute === "noface" && noface.voiceSource !== "tts" && !voiceUpload) return setNotice("Hãy tải tệp giọng đọc trước khi tạo video No-face.");
    if (sourceRoute === "upload" && !sourceFile) return setNotice("Hãy chọn lại video nguồn trong phiên hiện tại trước.");
    if (sourceRoute === "avatar") {
      if (!avatar.costConfirmed) return setNotice("Hãy tích xác nhận ý định sử dụng credit HeyGen trước.");
      if (!window.confirm(`Gửi kịch bản sang HeyGen ngay bây giờ? Tác vụ có thể sử dụng credit của tài khoản${avatar.test ? " (đang bật test mode)" : ""}.`)) return setNotice("Đã hủy trước khi gọi HeyGen; chưa sử dụng credit.");
      setVideoTask("creating"); setTaskStartedAt(Date.now()); setTaskMessage("Đang kết nối local-agent..."); setHeygenComplete(false); setNotice("");
      try {
        const response = await fetch("/api/local-agent/heygen", { method: "POST", headers: { "Content-Type": "application/json", ...(secrets.heygen ? { "x-heygen-key": secrets.heygen } : {}) }, body: JSON.stringify({ confirmed: true, title: selectedScript?.hook, domainId, styleId, source: selectedVideos.find((item) => item.id === selectedScript?.sourceId) || null, script: selectedScript, voiceId: avatar.voiceId, avatarIds: avatar.avatarIds.split(/\r?\n|,/).map((item) => item.trim()).filter(Boolean), speed: Number(avatar.speed), targetSeconds: Number(avatar.duration), test: avatar.test }) });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Không thể gửi HeyGen job.");
        setSourceArtifact({ type: "heygen_request.json", route: "avatar", projectId: data.projectId, jobId: data.job.id, status: data.job.status });
        await waitForHeyGen(data.job.id, data.projectId);
      } catch (error) {
        setSourceArtifact(null);
        setNotice(error.message || "Không thể tạo video HeyGen.");
      } finally {
        setVideoTask(""); setTaskStartedAt(0); setTaskMessage("");
      }
      setEditPlan(null); setFinalApproved(false);
      return;
    } else if (sourceRoute === "noface") {
      setVideoTask("processing"); setTaskStartedAt(Date.now()); setTaskMessage("Đang chuẩn bị nguồn giọng và storyboard no-face...");
      try {
        if (noface.voiceSource === "tts") {
          setSourceArtifact({ type: "noface_plan.json", route: "no-face", voiceSource: noface.voiceSource, targetSeconds: Number(avatar.duration), scenes: [selectedScript.hook, selectedScript.body, selectedScript.cta], status: "storyboard-ready" });
          setNotice("Đã tạo storyboard no-face. Cần chọn voice thu sẵn để render MP4 cục bộ ở phiên bản hiện tại.");
        } else {
          const data = await uploadToLocalAgent(voiceUpload, "voice");
          setSourceArtifact({ type: "noface_plan.json", route: "no-face", voiceSource: noface.voiceSource, sourceFile: data.file, projectId: data.projectId, targetSeconds: Number(avatar.duration), scenes: [selectedScript.hook, selectedScript.body, selectedScript.cta], status: "ready" });
          setNotice("Đã tải voice vào local-agent; sẵn sàng dựng video no-face.");
        }
      } catch (error) { setSourceArtifact(null); setNotice(error.message || "Không thể chuẩn bị video no-face."); }
      finally { setVideoTask(""); setTaskStartedAt(0); setTaskMessage(""); }
    } else {
      setVideoTask("processing"); setTaskStartedAt(Date.now()); setTaskMessage("Đang sao chép video gốc an toàn vào local-agent...");
      try {
        const data = await uploadToLocalAgent(sourceFile, "source");
        setSourceArtifact({ type: "upload_manifest.json", route: "upload", file: upload, sourceFile: data.file, projectId: data.projectId, status: "ready" });
        setVideoPreviewUrl(URL.createObjectURL(sourceFile)); setPreviewKind("source"); setFinalVideoName(upload.name);
        setNotice("Video gốc đã được lưu trong project local-agent; sẵn sàng dựng.");
      } catch (error) { setSourceArtifact(null); setNotice(error.message || "Không thể tải video nguồn."); }
      finally { setVideoTask(""); setTaskStartedAt(0); setTaskMessage(""); }
    }
    setEditPlan(null); setFinalApproved(false);
  }

  async function createEditPlan(version = 1, feedbackOverride = "") {
    if (!sourceArtifact) return setNotice("Hãy chuẩn bị source video trước khi tạo edit plan.");
    if (!sourceArtifact.projectId || !sourceArtifact.sourceFile) return setNotice("Nguồn hiện tại chưa có file video/audio trong local-agent để dựng.");
    setBusy("edit"); setVideoTask("editing"); setTaskStartedAt(Date.now()); setTaskMessage("Đang gửi tác vụ dựng tới local-agent..."); setNotice("");
    try {
      const response = await fetch("/api/local-agent/edit", { method: "POST", headers: { "Content-Type": "application/json", ...(secrets.pexels ? { "x-pexels-key": secrets.pexels } : {}), ...(secrets.pixabay ? { "x-pixabay-key": secrets.pixabay } : {}) }, body: JSON.stringify({ projectId: sourceArtifact.projectId, sourceFile: sourceArtifact.sourceFile, styleId, videoMode: sourceRoute, targetSeconds: Number(avatar.duration), version, feedback: feedbackOverride, footer: brand.name, textOverlay: { ...textOverlay, lines: textOverlay.lines.split(/\r?\n/).map((item) => item.trim()).filter(Boolean) } }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      const result = await waitForAgentJob(data.job.id, "Agent đang dựng video...");
      const mediaUrl = `/api/local-agent/media?projectId=${encodeURIComponent(sourceArtifact.projectId)}&file=${encodeURIComponent(result.file)}`;
      setEditPlan(result.edit_plan); setVideoPreviewUrl(mediaUrl); setPreviewKind("final"); setFinalVideoName(result.file); setFinalApproved(false); setQa(QA_DEFAULT); setNotice(`Đã dựng xong phiên bản ${result.version} · MP4 1080x1920. Hãy xem toàn bộ video trước khi tải.`);
    } catch (error) { setNotice(error.message || "Không thể tạo edit plan."); }
    finally { setVideoTask(""); setBusy(""); setTaskStartedAt(0); setTaskMessage(""); }
  }

  async function submitFeedback() {
    const text = feedbackText.trim();
    if (!text || !editPlan) return setNotice("Hãy nhập feedback sau khi có edit plan/preview.");
    const nextVersion = Number(editPlan.version || 1) + 1;
    setFeedback((current) => [...current, { version: nextVersion, text, createdAt: new Date().toISOString() }]);
    setFeedbackText("");
    await createEditPlan(nextVersion, text);
  }

  function approveFinal() {
    if (!Object.values(qa).every(Boolean)) return setNotice("Cần hoàn thành toàn bộ QA trước khi duyệt final.");
    setFinalApproved(true); setNotice("Đã duyệt final. Publishing vẫn cần xác nhận riêng.");
  }

  function finalizeDistribution() {
    if (!finalApproved) return setNotice("Cần duyệt final trước khi chuẩn bị phân phối.");
    if (publish.mode === "skip") return setNotice("Đã ghi skip.json. Không có hành động bên ngoài.");
    if (!publish.platforms.length || !publish.profile || !publish.confirmed) return setNotice("Đăng thật cần nền tảng, profile và xác nhận hiện tại.");
    setNotice("Đã tạo publish.json ở trạng thái planned. Web không tự đăng; local-agent thực hiện sau xác nhận hành động.");
  }

  const artifacts = useMemo(() => ({
    "manifest.json": { schemaVersion: "3.0-finance-compatible", entryMode, domainPack: domain, contentFormat: format, brand, approvals: { researchApproved, scriptApproved, externalCostConfirmed: avatar.costConfirmed, finalApproved, publishingConfirmed: publish.confirmed } },
    "selected_videos.json": selectedVideos,
    "script_candidates.json": scripts,
    "approved_script.json": scriptApproved ? selectedScript : null,
    "voice_script_heygen.txt": scriptApproved ? selectedScript?.text : "",
    [sourceArtifact?.type || "source_pending.json"]: sourceArtifact,
    "edit_plan.json": editPlan,
    "edit_feedback.json": feedback,
    "qa_report.json": { checks: qa, approved: finalApproved },
    [publish.mode === "skip" ? "skip.json" : "publish.json"]: { ...publish, externalActionExecuted: false },
  }), [entryMode, domain, format, brand, researchApproved, scriptApproved, avatar.costConfirmed, finalApproved, publish, selectedVideos, scripts, selectedScript, sourceArtifact, editPlan, feedback, qa]);

  const progress = [researchApproved, scriptApproved, Boolean(sourceArtifact), Boolean(editPlan), finalApproved].filter(Boolean).length;
  const visibleScripts = scripts.filter((item) => item.sourceId === scriptSourceId && selectableScript(item));
  const videoTaskLabel = videoTask === "editing" ? "Đang edit..." : videoTask === "processing" ? "Đang xử lý video..." : "Đang tạo video...";

  return <main className={styles.page}>
    <header className={styles.topbar}><div><span className={styles.logo}>BF</span><div><strong>BrandFlow Executive Studio</strong><small>AI video workspace cho chuyên gia và doanh nhân</small></div></div><span className={styles.autosave}><Icon name="shield" /> Đã lưu tự động</span></header>

    <section className={styles.hero}><div><span className={styles.eyebrow}>PERSONAL BRAND VIDEO WORKSPACE</span><h1>Biến chuyên môn thành<br/><em>thương hiệu có sức ảnh hưởng.</em></h1><p>Tìm chủ đề tiềm năng, phát triển kịch bản, tạo video và hoàn thiện nội dung trong một quy trình duy nhất.</p></div><aside><small>TIẾN ĐỘ VIDEO</small><strong>{progress}/5 bước hoàn thành</strong><div className={styles.progress}><i style={{ width: `${progress / 5 * 100}%` }} /></div><span>{domain.name} · {selectedStyle.name}</span></aside></section>

    <button className={styles.settingsButton} onClick={() => {setSettingsOpen((value) => !value);setGuideOpen(false);}} aria-expanded={settingsOpen}><Icon name="gear"/><strong>Cài đặt</strong><small>Thương hiệu & API</small></button>
    <button className={styles.guideButton} onClick={() => {setGuideOpen((value) => !value);setSettingsOpen(false);}} aria-expanded={guideOpen}><Icon name="book"/><strong>Hướng dẫn lấy API</strong><small>Link và từng bước thiết lập</small></button>
    <nav className={styles.steps} aria-label="Quy trình tạo video">{[["2","Nghiên cứu"],["3","Kịch bản"],["4","Video nguồn"],["5","Dựng video"],["6","Thành phẩm"]].map(([step,label], index) => <a key={step} href={`#step-${step}`}><b>{index + 1}</b><span>{label}</span></a>)}</nav>
    {notice && <Status tone={notice.includes("cần") || notice.includes("Hãy") ? "warning" : "info"}>{notice}</Status>}
    {(videoTask || busy === "research") && <div className={styles.taskToast} role="status" aria-live="polite"><span className={styles.spinner}/><div><strong>{taskMessage || videoTaskLabel}</strong><small>Đã chạy {elapsedLabel(elapsedSeconds)} · Bạn có thể tiếp tục theo dõi ngay trên bước hiện tại.</small></div></div>}
    {settingsOpen && <Section number="CĐ" title="Cài đặt hệ thống" subtitle="Khóa API chỉ được giữ trong bộ nhớ của tab hiện tại và không nằm trong tệp dự án." state="Bảo mật theo phiên">
      <div className={styles.formGrid}><Field label="Tên thương hiệu"><input value={brand.name} onChange={(event) => setBrand({...brand,name:event.target.value})}/></Field><Field label="Định dạng nội dung"><select value={formatId} onChange={(event) => setFormatId(event.target.value)}>{contentFormats.map((item)=><option key={item.id} value={item.id}>{item.name}</option>)}</select></Field><Field label="Khách hàng mục tiêu"><textarea rows="2" value={brand.audience} onChange={(event) => setBrand({...brand,audience:event.target.value})}/></Field><Field label="Giọng thương hiệu"><textarea rows="2" value={brand.voice} onChange={(event) => setBrand({...brand,voice:event.target.value})}/></Field><Field label="Apify API Token"><input type="password" autoComplete="off" placeholder="••••••••••••" value={secrets.apify} onChange={(event)=>setSecrets({...secrets,apify:event.target.value})}/></Field><Field label="Kyma API Key"><input type="password" autoComplete="off" placeholder="••••••••••••" value={secrets.kyma} onChange={(event)=>setSecrets({...secrets,kyma:event.target.value})}/></Field><Field label="HeyGen API Key"><input type="password" autoComplete="off" placeholder="••••••••••••" value={secrets.heygen} onChange={(event)=>setSecrets({...secrets,heygen:event.target.value})}/></Field><Field label="Pexels API Key"><input type="password" autoComplete="off" placeholder="••••••••••••" value={secrets.pexels} onChange={(event)=>setSecrets({...secrets,pexels:event.target.value})}/></Field><Field label="Pixabay API Key"><input type="password" autoComplete="off" placeholder="••••••••••••" value={secrets.pixabay} onChange={(event)=>setSecrets({...secrets,pixabay:event.target.value})}/></Field></div>
      <div className={styles.securityNote}><Icon name="shield"/><span><strong>Không lưu khóa vào trình duyệt.</strong> Khi đóng hoặc tải lại tab, bạn cần nhập lại. Bản production nên cấu hình khóa tại Vercel Environment Variables hoặc kho bí mật phía máy chủ.</span></div>
      <div className={styles.actionRow}><span>{Object.values(secrets).filter(Boolean).length}/{API_GUIDES.length} dịch vụ được nhập khóa trong phiên</span><button className={styles.primary} onClick={()=>{setSettingsOpen(false);setNotice("Đã áp dụng cấu hình cho phiên hiện tại.");}}>Áp dụng cài đặt</button></div>
    </Section>}
    {guideOpen && <Section number="HD" title="Hướng dẫn lấy API" subtitle="Mỗi dịch vụ nên dùng một khóa riêng cho BrandFlow. Không gửi khóa qua tin nhắn hoặc lưu vào ảnh chụp màn hình." state={`${API_GUIDES.length} dịch vụ`}>
      <div className={styles.guideGrid}>{API_GUIDES.map((guide)=><article className={styles.guideCard} key={guide.id}><header><span>{guide.name.slice(0,2).toUpperCase()}</span><div><h3>{guide.name}</h3><p>{guide.purpose}</p></div></header><ol>{guide.steps.map((step)=><li key={step}>{step}</li>)}</ol><div className={styles.guideLinks}><a href={guide.home} target="_blank" rel="noreferrer">Trang chủ <Icon name="arrow"/></a><a href={guide.keyUrl} target="_blank" rel="noreferrer">Mở trang lấy API <Icon name="arrow"/></a></div><div className={styles.guideImageSlot}><span>Vị trí ảnh minh họa</span><small>Có thể bổ sung ảnh từng bước sau</small></div></article>)}</div>
      <div className={styles.securityNote}><Icon name="shield"/><span><strong>Lưu ý bảo mật:</strong> Chỉ dán API key trong mục Cài đặt của sản phẩm. Hãy dùng key riêng, giới hạn quyền và đặt hạn sử dụng nếu nhà cung cấp hỗ trợ.</span></div>
    </Section>}

    <div id="step-2"><Section number="01" title="Nghiên cứu nội dung nổi bật" subtitle="Khám phá video tiềm năng theo kênh, lượt xem, tương tác và lý do tạo sức hút." state={researchApproved ? "Đã chọn tham chiếu" : undefined}>
      <div className={styles.researchModes}><button className={research.mode === "topic" ? styles.selected : ""} onClick={()=>setResearch({...research,mode:"topic"})}><strong>Nghiên cứu theo chủ đề</strong><span>Dùng từ khóa + ngành/ngách, AI lọc độ liên quan</span></button><button className={research.mode === "channel" ? styles.selected : ""} onClick={()=>setResearch({...research,mode:"channel"})}><strong>Nghiên cứu theo kênh</strong><span>Lấy top video từ kênh đối thủ có sẵn</span></button></div>
      {research.mode === "topic" ? <div className={styles.researchPanel}><div className={styles.platforms}>{Object.entries(PLATFORM_LABELS).map(([id,label]) => <label key={id}><input type="checkbox" checked={research.platforms.includes(id)} onChange={() => togglePlatform(id)}/><span>{label}</span></label>)}</div><div className={styles.researchFields}><Field label="Từ khóa"><input placeholder="VD: cách build skill edit video trên Claude" value={research.keyword} onChange={(event) => setResearch({ ...research, keyword: event.target.value })}/></Field><Field label="Ngành/ngách"><input placeholder="VD: AI Claude" value={brand.niche} onChange={(event)=>setBrand({...brand,niche:event.target.value})}/></Field><Field label="Ngôn ngữ ưu tiên"><select value={research.language} onChange={(event)=>setResearch({...research,language:event.target.value})}><option value="Tiếng Việt">Tiếng Việt</option><option value="English">English</option><option value="Song ngữ Việt–Anh">Song ngữ Việt–Anh</option></select></Field><Field label="Khoảng thời gian"><select value={research.period} onChange={(event)=>setResearch({...research,period:event.target.value})}><option value="30d">30 ngày</option><option value="90d">90 ngày</option><option value="6m">6 tháng</option><option value="12m">12 tháng</option></select></Field></div><button className={styles.primary} onClick={runResearch} disabled={Boolean(busy)}><Icon name="search" />{busy === "research" ? "Đang nghiên cứu..." : "Nghiên cứu nội dung"}</button></div> : <div className={styles.researchPanel}><p className={styles.channelHint}>Nếu bạn có sẵn link kênh để nghiên cứu thì dán vào đây</p><Field label="Link kênh YouTube, TikTok hoặc Facebook — mỗi dòng một link"><textarea rows="5" placeholder={"https://youtube.com/@tenkenh\nhttps://tiktok.com/@tenkenh\nhttps://facebook.com/tenkenh"} value={research.channelUrls} onChange={(event)=>setResearch({...research,channelUrls:event.target.value})}/></Field><div className={styles.channelOptions}><Field label="Khoảng thời gian"><select value={research.period} onChange={(event)=>setResearch({...research,period:event.target.value})}><option value="30d">30 ngày</option><option value="90d">90 ngày</option><option value="6m">6 tháng</option><option value="12m">12 tháng</option></select></Field><span>Agent tự nhận diện nền tảng, quét tối đa 100 video/kênh và chọn top 20.</span></div><button className={styles.primary} onClick={runResearch} disabled={Boolean(busy)}><Icon name="search" />{busy === "research" ? "Đang nghiên cứu..." : "Nghiên cứu nội dung"}</button></div>}
      {busy === "research" && <div className={styles.inlineJob}><span className={styles.spinner}/><div><strong>{taskMessage || "Đang nghiên cứu nội dung..."}</strong><small>Đã chạy {elapsedLabel(elapsedSeconds)} · Không dùng phần trăm giả.</small></div></div>}
      <div className={styles.tableWrap}><table><thead><tr><th>Chọn</th><th>Kênh</th><th>Video nổi bật</th><th>Link</th><th>Lượt xem</th><th>Like</th><th>Bình luận</th><th>Chia sẻ</th><th>Tương tác</th><th>Lý do nổi bật</th></tr></thead><tbody>{rows.map((row) => {const picked=selectedVideos.some((item)=>item.id===row.id);return <tr key={row.id} className={picked ? styles.activeRow : ""}><td><button className={styles.radioButton} aria-label={`Chọn ${row.title}`} aria-pressed={picked} onClick={() => toggleVideo(row)}>{picked && <Icon name="check" />}</button></td><td><span className={`${styles.platform} ${styles[row.platform]}`}>{PLATFORM_LABELS[row.platform] || row.platform}</span><small>{row.channel}</small></td><td><strong>{row.title}</strong></td><td><a href={row.url} target="_blank" rel="noreferrer">Mở video</a></td><td>{row.viewsText}</td><td>{row.likesText}</td><td>{row.commentsText}</td><td>{row.sharesText}</td><td>{row.engagementPct == null ? "—" : `${row.engagementPct}%`}</td><td>{row.viralReason}</td></tr>})}</tbody></table>{!rows.length && <div className={styles.empty}>Chọn một cách nghiên cứu ở trên để bắt đầu. Kết quả live sẽ không được lấp bằng dữ liệu demo.</div>}</div>
      {selectedVideos.length > 0 && <div className={styles.selectionBar}><span><strong>{selectedVideos.length} video đã chọn</strong><small>Các video sẽ xuất hiện trong hàng đợi viết kịch bản.</small></span><button className={styles.primary} onClick={()=>{setResearchApproved(true);setNotice(`Đã đưa ${selectedVideos.length} video vào hàng đợi viết kịch bản.`);}}>Đưa vào hàng đợi</button></div>}
    </Section></div>

    <div id="step-3"><Section number="02" title="Phát triển kịch bản" subtitle="Tạo 3 hướng tiếp cận, chỉnh sửa toàn văn và rà soát độ tin cậy trước khi sản xuất." state={scriptApproved ? "Đã duyệt kịch bản" : undefined}>
      <div className={styles.horizontalTabs}><button className={scriptMode==="write"?styles.selected:""} onClick={()=>setScriptMode("write")}>Viết kịch bản</button><button className={scriptMode==="import"?styles.selected:""} onClick={()=>setScriptMode("import")}>Nhập kịch bản có sẵn</button></div>
      {scriptMode === "write" && <div className={styles.scriptQueue}>{researchApproved ? selectedVideos.map((video)=>{const sourceScripts=scripts.filter((item)=>item.sourceId===video.id);const ready=sourceScripts.length===3&&sourceScripts.every(validScriptCandidate);return <article key={video.id} className={scriptSourceId===video.id?styles.queueActive:""}><div><small>{PLATFORM_LABELS[video.platform] || video.platform}</small><strong>{video.title}</strong><span>{video.channel}</span></div><button className={ready?styles.secondary:styles.primary} onClick={()=>{setScriptSourceId(video.id);if(ready){setSelectedScriptId(sourceScripts[0]?.id||"");}else generateScripts(video);}} disabled={busy==="script"}>{busy==="script"&&scriptSourceId===video.id?"Đang tạo...":ready?"Xem 3 kịch bản":sourceScripts.length?"Tạo lại 3 kịch bản":"Tạo 3 kịch bản"}</button></article>}) : <div className={styles.empty}>Chưa có video trong hàng đợi. Hãy chọn video ở bước Nghiên cứu.</div>}</div>}
      {scriptMode === "import" && <div className={styles.importBox}><Field label="Kịch bản có sẵn"><textarea rows="10" placeholder="Dán toàn bộ kịch bản của bạn vào đây…" value={importedScript} onChange={(event)=>setImportedScript(event.target.value)}/></Field><button className={styles.primary} onClick={useImportedScript}>Sử dụng kịch bản này</button></div>}
      {visibleScripts.length > 0 && <div className={styles.scriptTabs}>{visibleScripts.map((item,index) => <button key={item.id} aria-pressed={selectedScript?.id === item.id} className={selectedScript?.id === item.id ? styles.selected : ""} onClick={() => { setSelectedScriptId(item.id); setScriptApproved(false); }}><small>Phương án {index+1}</small><strong>{item.angle}</strong><span>{item.hook}</span></button>)}</div>}
      {selectedScript && <div className={styles.scriptEditor}><div><Field label="Mở đầu · 0–3 giây"><textarea rows="2" value={selectedScript.hook} onChange={(event) => updateScript("hook", event.target.value)}/></Field><Field label="Nội dung chính"><textarea rows="8" value={selectedScript.body} onChange={(event) => updateScript("body", event.target.value)}/></Field><Field label="Kêu gọi hành động"><textarea rows="2" value={selectedScript.cta} onChange={(event) => updateScript("cta", event.target.value)}/></Field></div><aside><h3>Phân tích sáng tạo</h3>{Object.entries(selectedScript.analysis || {}).map(([key,value]) => <div key={key}><strong>{key}</strong><p>{value}</p></div>)}<h3>Rà soát nội dung</h3>{(selectedScript.claimCheck || []).map((item,index) => <div className={item.level === "warning" ? styles.claimWarning : styles.claimOk} key={`${item.rule}-${index}`}><strong>{item.level === "warning" ? "Cần xem lại" : "Đã kiểm tra"}</strong><p>{item.label}</p></div>)}</aside></div>}
      {selectedScript && <label className={styles.approval}><input type="checkbox" checked={scriptApproved} onChange={(event) => setScriptApproved(event.target.checked)}/><span><strong>Duyệt kịch bản đang mở</strong><small>Kịch bản được duyệt sẽ dùng để tạo và dựng video.</small></span></label>}
    </Section></div>

    <div id="step-4"><Section number="03" title="Tạo video nguồn" subtitle="Chọn AI Avatar, video không lộ mặt hoặc tải lên footage bạn đã quay." state={sourceArtifact ? "Video đã chuẩn bị" : undefined}>
      <div className={styles.modeGrid}>{[["avatar","Video HeyGen Avatar","Người dẫn AI theo thương hiệu"],["noface","Video No-face","Giọng đọc và hình ảnh minh họa"],["upload","Upload video gốc có sẵn","Dựng lại từ footage của bạn"]].map(([id,name,desc]) => <button key={id} className={sourceRoute === id ? styles.selected : ""} onClick={() => { setSourceRoute(id); setSourceArtifact(null); }}><strong>{name}</strong><span>{desc}</span></button>)}</div>
      {sourceRoute === "avatar" && <><Status tone={localAgent.online && localAgent.heygen ? "info" : "warning"}>{!localAgent.checked ? "Đang kiểm tra local-agent..." : localAgent.online && localAgent.heygen ? `HeyGen Photo Avatar III và local-agent đã sẵn sàng${localAgent.defaults.voiceConfigured && localAgent.defaults.avatarConfigured ? " · Có Voice/Avatar mặc định trong .env.local" : ""}. Không tự chuyển sang Avatar IV nếu tài khoản không hỗ trợ.` : "Local-agent chưa chạy hoặc chưa đọc được HEYGEN_API_KEY. Hãy khởi động bằng npm run dev:full."}</Status><div className={styles.formGrid}><Field label="HeyGen Voice ID" help="Có thể để trống nếu HEYGEN_VOICE_ID đã có trong .env.local."><input placeholder="Dùng mặc định từ .env.local" value={avatar.voiceId} onChange={(event) => setAvatar({ ...avatar, voiceId: event.target.value })}/></Field><Field label="Photo Avatar III IDs — phân cách bằng dấu phẩy hoặc xuống dòng" help="Chỉ dùng Photo Avatar III; không tự fallback sang engine khác."><textarea rows="2" placeholder="Dùng mặc định từ .env.local" value={avatar.avatarIds} onChange={(event) => setAvatar({ ...avatar, avatarIds: event.target.value })}/></Field><Field label="Thời lượng mục tiêu"><select value={avatar.duration} onChange={(event)=>setAvatar({...avatar,duration:Number(event.target.value)})}>{[30,45,55,60,90].map((value)=><option key={value} value={value}>{value} giây{value===55?" · đề xuất":""}</option>)}</select></Field><Field label="Voice speed"><input type="number" min="0.5" max="1.5" step="0.05" value={avatar.speed} onChange={(event) => setAvatar({ ...avatar, speed: event.target.value })}/></Field><label className={styles.checkCard}><input type="checkbox" checked={avatar.test} onChange={(event) => setAvatar({ ...avatar, test: event.target.checked })}/><span><strong>HeyGen test mode</strong><small>Ưu tiên bản test trước production.</small></span></label><label className={styles.checkCard}><input type="checkbox" checked={avatar.costConfirmed} onChange={(event) => setAvatar({ ...avatar, costConfirmed: event.target.checked })}/><span><strong>Tôi hiểu tác vụ có thể dùng credit</strong><small>Khi bấm tạo video, hệ thống vẫn hỏi xác nhận lần cuối.</small></span></label><label className={styles.checkCard}><input type="checkbox" checked={avatar.notify} onChange={async(event)=>{const checked=event.target.checked;setAvatar({...avatar,notify:checked});if(checked&&typeof Notification!=="undefined"&&Notification.permission==="default")await Notification.requestPermission();}}/><span><strong>Thông báo khi HeyGen xong</strong><small>Hiển thị thông báo trình duyệt nếu bạn cho phép.</small></span></label></div></>}
      {sourceRoute === "noface" && <div className={styles.formGrid}><Field label="Nguồn giọng"><select value={noface.voiceSource} onChange={(event) => {setNoface({ ...noface, voiceSource: event.target.value });setVoiceUpload(null);}}><option value="tts">Giọng AI</option><option value="recorded">Voice thu sẵn</option><option value="approved-audio">Audio đã duyệt</option></select></Field>{noface.voiceSource !== "tts" && <Field label="Tải tệp giọng đọc"><input type="file" accept="audio/*" onChange={(event)=>setVoiceUpload(event.target.files?.[0] || null)}/>{voiceUpload&&<small>{voiceUpload.name} · {(voiceUpload.size/1024/1024).toFixed(1)} MB</small>}</Field>}</div>}
      {sourceRoute === "upload" && <Field label="Chọn video nguồn"><input type="file" accept="video/*" onChange={(event) => { const file = event.target.files?.[0]; setSourceFile(file || null); setUpload(file ? { name: file.name, size: file.size, type: file.type, lastModified: file.lastModified } : null); setSourceArtifact(null); }}/>{upload && <small>{upload.name} · {(upload.size / 1024 / 1024).toFixed(1)} MB</small>}</Field>}
      <div className={styles.actionRow}><span>{sourceArtifact?.status === "ready" ? "Video nguồn đã sẵn sàng" : sourceArtifact ? "Tác vụ video đã được tạo" : "Chưa chuẩn bị video nguồn"}</span><button className={styles.primary} onClick={createSourceArtifact} disabled={videoTask || (!scriptApproved && entryMode !== "edit" && entryMode !== "publish")}>{videoTask && videoTask !== "editing" ? videoTaskLabel : sourceRoute === "avatar" ? "Tạo video HeyGen" : "Chuẩn bị video"}</button></div>
      {videoTask && videoTask !== "editing" && <div className={styles.inlineJob}><span className={styles.spinner}/><div><strong>{taskMessage || videoTaskLabel}</strong><small>Đã chạy {elapsedLabel(elapsedSeconds)} · Thời gian thực tế phụ thuộc độ dài video và hàng đợi nhà cung cấp.</small></div></div>}
      {heygenComplete && sourceArtifact?.route === "avatar" && <div className={styles.successBanner}><div><Icon name="check"/><span><strong>Video HeyGen đã hoàn thành</strong><small>Hãy kiểm tra nhanh video nguồn, sau đó chuyển sang bước Dựng video.</small></span></div><aside><a href="#step-6" className={styles.secondary}>Xem video HeyGen</a><a href="#step-5" className={styles.primary}>Qua bước Edit</a></aside></div>}
    </Section></div>

    <div id="step-5"><Section number="04" title="Chọn phong cách dựng" subtitle="Cá nhân hóa nhịp cắt, phụ đề, chuyển cảnh và hình ảnh minh họa theo dấu ấn thương hiệu." state={editPlan ? `Phiên bản ${editPlan.version}` : undefined}>
      <div className={styles.styleGrid}>{editStyles.map((item) => <button key={item.id} className={styleId === item.id ? styles.selected : ""} onClick={() => { setStyleId(item.id); setEditPlan(null); }}><div>{item.palette.map((color) => <i key={color} style={{ background: color }}/>)}</div><strong>{item.name}{domain.defaultStyle === item.id && <small>Đề xuất</small>}</strong><span>{item.bestFor}</span><p>{item.description}</p></button>)}</div>
      <div className={styles.overlayEditor}>
        <header><div><small>FINANCE EDITORIAL TRAINING PACK</small><h3>Thiết lập Text Overlay</h3><p>Kicker nhỏ màu nhấn + headline Montserrat ExtraBold trên nền tối, ưu tiên các beat proof/metaphor và không che hook/CTA.</p></div><label className={styles.overlayToggle}><input type="checkbox" checked={textOverlay.enabled} onChange={(event)=>setTextOverlay({...textOverlay,enabled:event.target.checked})}/><span>{textOverlay.enabled ? "Đang bật" : "Đã tắt"}</span></label></header>
        {textOverlay.enabled && <><div className={styles.overlayGrid}>
          <Field label="Kicker nhỏ"><input value={textOverlay.kicker} maxLength="60" placeholder="ĐIỂM CẦN NHỚ" onChange={(event)=>setTextOverlay({...textOverlay,kicker:event.target.value})}/></Field>
          <Field label="Vị trí"><select value={textOverlay.position} onChange={(event)=>setTextOverlay({...textOverlay,position:event.target.value})}><option value="top">Phía trên · giống mẫu Finance</option><option value="middle">Giữa khung hình</option><option value="lower">Phía dưới · trên vùng subtitle</option></select></Field>
          <Field label="Căn chữ"><select value={textOverlay.align} onChange={(event)=>setTextOverlay({...textOverlay,align:event.target.value})}><option value="left">Căn trái · giống mẫu Finance</option><option value="center">Căn giữa</option><option value="right">Căn phải</option></select></Field>
          <Field label={`Cỡ headline · ${textOverlay.fontSize}px`}><input type="range" min="42" max="96" step="2" value={textOverlay.fontSize} onChange={(event)=>setTextOverlay({...textOverlay,fontSize:Number(event.target.value)})}/></Field>
          <Field label={`Ký tự tối đa mỗi dòng · ${textOverlay.maxCharsPerLine}`}><input type="range" min="12" max="34" step="1" value={textOverlay.maxCharsPerLine} onChange={(event)=>setTextOverlay({...textOverlay,maxCharsPerLine:Number(event.target.value)})}/></Field>
          <Field label={`Độ đậm nền · ${Math.round(textOverlay.backgroundOpacity*100)}%`}><input type="range" min="0.2" max="0.95" step="0.05" value={textOverlay.backgroundOpacity} onChange={(event)=>setTextOverlay({...textOverlay,backgroundOpacity:Number(event.target.value)})}/></Field>
        </div><div className={styles.overlayColors}><label><span>Màu headline</span><input type="color" value={textOverlay.textColor} onChange={(event)=>setTextOverlay({...textOverlay,textColor:event.target.value})}/></label><label><span>Màu nhấn/kicker</span><input type="color" value={textOverlay.accentColor} onChange={(event)=>setTextOverlay({...textOverlay,accentColor:event.target.value})}/></label><label><span>Màu nền</span><input type="color" value={textOverlay.backgroundColor} onChange={(event)=>setTextOverlay({...textOverlay,backgroundColor:event.target.value})}/></label><label><input type="checkbox" checked={textOverlay.uppercase} onChange={(event)=>setTextOverlay({...textOverlay,uppercase:event.target.checked})}/><span>Viết hoa headline</span></label><label><input type="checkbox" checked={textOverlay.accentStripe} onChange={(event)=>setTextOverlay({...textOverlay,accentStripe:event.target.checked})}/><span>Thêm vạch nhấn trái</span></label></div>
        <div className={styles.overlayCopy}><Field label="Headline tùy chỉnh — mỗi dòng ứng với một beat proof/metaphor" help="Để trống thì agent tự rút tối đa 10 từ từ lời thoại. Không nên lặp nguyên subtitle."><textarea rows="5" placeholder={"VÌ SAO GIÁ VÀNG GIẢM?\nBA TÍN HIỆU CẦN THEO DÕI"} value={textOverlay.lines} onChange={(event)=>setTextOverlay({...textOverlay,lines:event.target.value})}/></Field><button className={styles.secondary} onClick={()=>setTextOverlay({...textOverlay,lines:overlaySuggestions(selectedScript)})} disabled={!selectedScript}>Lấy gợi ý từ kịch bản</button></div></>}
      </div>
      <div className={styles.actionRow}><span>{entryMode === "publish" ? "Bản hoàn chỉnh không cần dựng lại" : `${selectedStyle.cutRhythm} · ${selectedStyle.caption}`}</span><button className={styles.primary} onClick={() => createEditPlan(1)} disabled={entryMode === "publish" || !sourceArtifact || Boolean(busy)}>{busy === "edit" ? "Đang dựng video..." : "Dựng video hoàn chỉnh"}</button></div>
      {videoTask === "editing" && <div className={styles.inlineJob}><span className={styles.spinner}/><div><strong>{taskMessage || "Đang edit..."}</strong><small>Đã chạy {elapsedLabel(elapsedSeconds)} · Video sẽ tự xuất hiện khi file MP4 hoàn thành.</small></div></div>}
      {editPlan && <div className={styles.beats}>{editPlan.beats.map((beat) => <article key={beat.id}><span>{beat.start}s–{beat.end}s</span><strong>{beat.visualRole} · {beat.assetSource}</strong><p>{beat.spokenMeaning}</p><small>{beat.cutReason || `${beat.captionTreatment} · ${beat.textEffect} · ${beat.transition}`}</small>{beat.stockProviders?.length > 0 && <small>Nguồn dự phòng: {beat.stockProviders.join(" → ")}</small>}</article>)}</div>}
      {editPlan && <div className={styles.feedback}><Field label="Feedback sau preview"><textarea rows="3" placeholder="VD: 00:12 chữ nhỏ; đổi chart; giảm nhạc nền..." value={feedbackText} onChange={(event) => setFeedbackText(event.target.value)}/></Field><button className={styles.secondary} onClick={submitFeedback}>Gửi feedback & tạo version mới</button>{feedback.map((item) => <p key={`${item.version}-${item.createdAt}`}><strong>V{item.version}</strong> · {item.text}</p>)}</div>}
    </Section></div>

    <div id="step-6"><Section number="05" title="Video thành phẩm" subtitle="Xem video hoàn chỉnh, tải bản MP4 hoặc gửi yêu cầu chỉnh sửa thêm." state={previewKind === "final" ? "Thành phẩm sẵn sàng" : videoPreviewUrl ? "Video nguồn sẵn sàng" : "Đang chờ thành phẩm"}>
      <div className={styles.finalStage}><div className={`${styles.finalReview} ${videoTask ? styles.videoDimmed : ""}`} aria-busy={Boolean(videoTask)}><div className={styles.videoColumn}>{videoPreviewUrl ? <><span className={styles.previewBadge}>{previewKind === "final" ? "VIDEO THÀNH PHẨM" : "VIDEO NGUỒN · CHƯA EDIT"}</span><video controls preload="metadata" src={videoPreviewUrl}/></> : <div className={styles.videoPlaceholder}><Icon name="arrow"/><strong>Video thành phẩm sẽ tự xuất hiện tại đây</strong><small>Sau khi bộ dựng hoàn tất, file MP4 được nạp tự động — không cần upload lại.</small></div>}{videoPreviewUrl&&<a className={styles.downloadVideo} href={videoPreviewUrl} download={previewKind === "final" ? "final.mp4" : finalVideoName || "source.mp4"}><Icon name="download"/> {previewKind === "final" ? "Tải video MP4" : "Tải video nguồn"}</a>}</div><div className={styles.revisionPanel}><Field label="Yêu cầu chỉnh sửa"><textarea rows="10" placeholder="VD: 00:12 tăng cỡ chữ; 00:27 đổi hình minh họa; giảm nhạc nền…" value={feedbackText} disabled={Boolean(videoTask)} onChange={(event)=>setFeedbackText(event.target.value)}/></Field><button className={styles.primary} disabled={Boolean(videoTask)||!editPlan||!feedbackText.trim()||Boolean(busy)} onClick={submitFeedback}>{videoTask==="editing"?"Đang edit...":"Edit lại theo yêu cầu bổ sung"}</button>{feedback.length>0&&<div className={styles.revisionHistory}><strong>Lịch sử yêu cầu</strong>{feedback.map((item)=><p key={item.createdAt}>Phiên bản {item.version} · {item.text}</p>)}</div>}</div></div>{videoTask&&<div className={styles.processingOverlay} role="status" aria-live="polite"><span className={styles.spinner}/><strong>{taskMessage || videoTaskLabel}</strong><small>Đã chạy {elapsedLabel(elapsedSeconds)} · Video sẽ tự nạp khi hoàn tất.</small></div>}</div>
    </Section></div>
  </main>;
}
