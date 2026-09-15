"use client";

import { useEffect, useMemo, useState } from "react";
import editStyles from "@/config/edit-styles.json";
import { DEMO_TRENDS } from "@/lib/demo-data";

const Icon = ({ name, size = 20 }) => {
  const paths = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
    search: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
    pen: <><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4Z"/></>,
    video: <><rect x="3" y="5" width="14" height="14" rx="2"/><path d="m17 10 4-2v8l-4-2Z"/></>,
    library: <><path d="M4 19.5V5a2 2 0 0 1 2-2h12v16H6a2 2 0 0 0-2 2Z"/><path d="M8 7h6M8 11h6"/></>,
    settings: <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3V2.8h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z"/></>,
    spark: <><path d="m12 3-1.2 4.1A5.5 5.5 0 0 1 7.1 11L3 12l4.1 1.2a5.5 5.5 0 0 1 3.7 3.7L12 21l1.2-4.1a5.5 5.5 0 0 1 3.7-3.7L21 12l-4.1-1.2a5.5 5.5 0 0 1-3.7-3.7Z"/></>,
    check: <path d="m5 12 4 4L19 6"/>,
    arrow: <path d="m9 18 6-6-6-6"/>,
    play: <path d="m8 5 11 7-11 7Z"/>,
    bolt: <path d="m13 2-8 12h7l-1 8 8-12h-7Z"/>,
    download: <><path d="M12 3v12m0 0 4-4m-4 4-4-4"/><path d="M5 20h14"/></>,
    external: <><path d="M14 4h6v6"/><path d="m20 4-9 9"/><path d="M18 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h6"/></>,
    user: <><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></>,
    layers: <><path d="m12 2 9 5-9 5-9-5Z"/><path d="m3 12 9 5 9-5M3 17l9 5 9-5"/></>,
    clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
  };
  return <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>;
};

const NAV = [
  { id: "overview", label: "Tổng quan", icon: "grid" },
  { id: "research", label: "Research", icon: "search" },
  { id: "script", label: "Kịch bản", icon: "pen" },
  { id: "production", label: "Sản xuất", icon: "video" },
  { id: "library", label: "Thư viện", icon: "library" },
];

const INITIAL_SCRIPT = {
  hook: "Nếu video của bạn có nhiều lượt xem nhưng không tạo ra khách hàng, có thể bạn đang tối ưu nhầm thứ.",
  body: "Người xem không cần thêm một danh sách kiến thức. Họ cần nhận ra vấn đề của mình, thấy một bằng chứng đủ rõ và biết hành động tiếp theo. Vì vậy, mỗi video chỉ nên giữ một ý chính: mở bằng tình huống thật, giải thích bằng một ví dụ dễ hình dung, rồi chốt bằng một bước nhỏ họ có thể làm ngay hôm nay.",
  cta: "Lưu video này và theo dõi để nhận thêm những khung nội dung có thể áp dụng ngay.",
};

function formatViews(value) {
  return new Intl.NumberFormat("vi-VN", { notation: "compact", maximumFractionDigits: 1 }).format(value || 0);
}

export default function Studio() {
  const [active, setActive] = useState("overview");
  const [brand, setBrand] = useState({ name: "SFI Academy", niche: "tài chính và đầu tư", audience: "người đi làm muốn đầu tư có hệ thống", voice: "Rõ ràng, điềm tĩnh, có bằng chứng" });
  const [trends, setTrends] = useState(DEMO_TRENDS);
  const [selectedTrend, setSelectedTrend] = useState(DEMO_TRENDS[0]);
  const [script, setScript] = useState(INITIAL_SCRIPT);
  const [styleId, setStyleId] = useState("editorial-proof");
  const [videoMode, setVideoMode] = useState("avatar");
  const [researching, setResearching] = useState(false);
  const [writing, setWriting] = useState(false);
  const [researchMode, setResearchMode] = useState("demo");
  const [notice, setNotice] = useState("");
  const [job, setJob] = useState(null);
  const [progress, setProgress] = useState(0);

  const selectedStyle = useMemo(() => editStyles.find((item) => item.id === styleId) || editStyles[0], [styleId]);
  const scriptLength = `${script.hook} ${script.body} ${script.cta}`.trim().length;

  useEffect(() => {
    const saved = window.localStorage.getItem("brandflow-project");
    if (!saved) return;
    try {
      const data = JSON.parse(saved);
      if (data.brand) setBrand(data.brand);
      if (data.script) setScript(data.script);
      if (data.styleId) setStyleId(data.styleId);
      if (data.videoMode) setVideoMode(data.videoMode);
    } catch {}
  }, []);

  useEffect(() => {
    window.localStorage.setItem("brandflow-project", JSON.stringify({ brand, script, styleId, videoMode }));
  }, [brand, script, styleId, videoMode]);

  useEffect(() => {
    if (!job || progress >= 100) return;
    const timer = window.setInterval(() => setProgress((value) => Math.min(100, value + (value < 55 ? 7 : 4))), 360);
    return () => window.clearInterval(timer);
  }, [job, progress]);

  async function runResearch() {
    setResearching(true);
    setNotice("");
    try {
      const response = await fetch("/api/research", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ niche: brand.niche }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      setTrends(data.items);
      setSelectedTrend(data.items[0]);
      setResearchMode(data.mode);
      setNotice(data.mode === "live" ? "Đã lấy dữ liệu YouTube thật qua Apify." : "Đang dùng dữ liệu demo an toàn; thêm APIFY_API_TOKEN để research live.");
    } catch (error) {
      setNotice(error.message || "Không thể research lúc này.");
    } finally {
      setResearching(false);
    }
  }

  async function writeScript() {
    setWriting(true);
    setNotice("");
    try {
      const response = await fetch("/api/generate-script", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ brandName: brand.name, niche: brand.niche, audience: brand.audience, voice: brand.voice, trendTitle: selectedTrend?.title, trendHook: selectedTrend?.hook }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      setScript({ hook: data.hook, body: data.body, cta: data.cta });
      setNotice(data.sourceMode === "live" ? `Kịch bản được tạo bằng ${data.model}.` : "Kịch bản demo đã sẵn sàng; thêm KYMA_API_KEY để dùng AI live.");
      setActive("script");
    } catch (error) {
      setNotice(error.message || "Không thể tạo kịch bản lúc này.");
    } finally {
      setWriting(false);
    }
  }

  async function startPipeline() {
    setNotice("");
    const response = await fetch("/api/pipeline", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ brand, niche: brand.niche, source: selectedTrend, script, production: { videoMode, editStyle: selectedStyle } }),
    });
    const data = await response.json();
    setJob(data);
    setProgress(4);
    setActive("production");
  }

  function downloadManifest() {
    if (!job?.manifest) return;
    const blob = new Blob([JSON.stringify(job.manifest, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${job.jobId.toLowerCase()}-manifest.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-mark"><span className="brand-symbol"><Icon name="spark" size={19}/></span><span>BrandFlow</span></div>
        <nav aria-label="Điều hướng chính">
          <p className="nav-eyebrow">Studio</p>
          {NAV.map((item) => <button key={item.id} className={`nav-item ${active === item.id ? "active" : ""}`} onClick={() => setActive(item.id)}><Icon name={item.icon}/><span>{item.label}</span>{item.id === "production" && job && <span className="nav-dot"/>}</button>)}
          <p className="nav-eyebrow nav-space">Không gian</p>
          <button className="nav-item"><Icon name="layers"/><span>Brand kit</span></button>
          <button className="nav-item"><Icon name="settings"/><span>Cài đặt</span></button>
        </nav>
        <div className="sidebar-card">
          <span className="status-dot"/> Demo mode
          <p>Chạy toàn bộ trải nghiệm mà không tốn API credit.</p>
        </div>
        <div className="profile"><div className="avatar">BH</div><div><strong>{brand.name || "Brand owner"}</strong><span>Workspace cá nhân</span></div></div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div><p className="eyebrow">AI VIDEO OPERATING SYSTEM</p><h1>{NAV.find((item) => item.id === active)?.label || "Studio"}</h1></div>
          <div className="top-actions"><span className="save-state"><Icon name="check" size={16}/> Đã tự lưu</span><button className="button secondary" onClick={() => setActive("production")}><Icon name="play" size={17}/> Xem demo</button><button className="button primary" onClick={startPipeline}><Icon name="bolt" size={17}/> Tạo video</button></div>
        </header>

        {notice && <div className="notice" role="status"><Icon name="spark" size={18}/><span>{notice}</span><button aria-label="Đóng thông báo" onClick={() => setNotice("")}>×</button></div>}

        {active === "overview" && <Overview brand={brand} setBrand={setBrand} setActive={setActive} startPipeline={startPipeline}/>} 
        {active === "research" && <Research brand={brand} setBrand={setBrand} trends={trends} selectedTrend={selectedTrend} setSelectedTrend={setSelectedTrend} runResearch={runResearch} researching={researching} researchMode={researchMode} writeScript={writeScript} writing={writing}/>} 
        {active === "script" && <ScriptEditor script={script} setScript={setScript} scriptLength={scriptLength} writeScript={writeScript} writing={writing} setActive={setActive}/>} 
        {active === "production" && <Production styles={editStyles} styleId={styleId} setStyleId={setStyleId} selectedStyle={selectedStyle} videoMode={videoMode} setVideoMode={setVideoMode} script={script} brand={brand} job={job} progress={progress} startPipeline={startPipeline} downloadManifest={downloadManifest}/>} 
        {active === "library" && <Library job={job} style={selectedStyle} brand={brand} downloadManifest={downloadManifest}/>} 
      </main>
    </div>
  );
}

function Overview({ brand, setBrand, setActive, startPipeline }) {
  const pipeline = [
    { id: "01", title: "Research tín hiệu", text: "Tìm nội dung breakout đúng ngách, xếp hạng theo tỷ lệ view/sub.", icon: "search", action: "research" },
    { id: "02", title: "Viết có góc nhìn", text: "Học cấu trúc hiệu quả, không sao chép câu chữ của nguồn.", icon: "pen", action: "script" },
    { id: "03", title: "Tạo hình & giọng", text: "Avatar HeyGen hoặc no-face, giữ đúng giọng thương hiệu.", icon: "user", action: "production" },
    { id: "04", title: "Edit có chủ đích", text: "Mỗi luận điểm đi cùng một hành động hình ảnh và lớp QA.", icon: "video", action: "production" },
  ];
  return <div className="content-grid">
    <section className="hero span-8">
      <div className="hero-copy"><span className="pill dark"><span className="pulse"/> Research → Script → Video → Edit</span><h2>Một hệ thống sản xuất video.<br/><em>Không phải thêm một tool AI.</em></h2><p>Biến tín hiệu đang tăng trưởng thành video thương hiệu cá nhân có quan điểm, có bằng chứng và đủ đẹp để đăng.</p><div className="hero-actions"><button className="button light" onClick={() => setActive("research")}>Bắt đầu một video <Icon name="arrow" size={17}/></button><button className="text-button" onClick={() => setActive("production")}>Khám phá style edit</button></div></div>
      <div className="hero-visual" aria-label="Mô phỏng video dọc"><div className="phone"><div className="phone-top"/><div className="video-gradient"><span className="mini-tag">EDITORIAL PROOF</span><div className="face-orb"><Icon name="user" size={42}/></div><strong>Đừng chỉ nói hay.<br/><mark>Hãy chứng minh.</mark></strong><div className="caption-lines"><i/><i/></div><div className="video-progress"><b/></div></div></div><div className="floating-card fc-one"><Icon name="check" size={16}/><span>Voice aligned</span></div><div className="floating-card fc-two"><span>15.6×</span> breakout</div></div>
    </section>
    <section className="metrics span-4">
      <div className="section-heading"><div><span className="kicker">Tuần này</span><h3>Sức khỏe pipeline</h3></div><span className="pill success"><span className="status-dot"/> Sẵn sàng</span></div>
      <div className="metric-list"><Metric value="12" label="Video hoàn tất" delta="+20%"/><Metric value="48m" label="Tiết kiệm / video" delta="Tự động"/><Metric value="96%" label="QA pass rate" delta="Ổn định"/></div>
      <div className="cost-card"><div><span>Chi phí dự kiến</span><strong>38.000đ</strong></div><small>/ video 55 giây</small><div className="cost-bar"><i/></div><p>Thấp hơn 87% so với quy trình thuê ngoài.</p></div>
    </section>
    <section className="panel span-8">
      <div className="section-heading"><div><span className="kicker">Luồng cốt lõi</span><h3>Từ tín hiệu đến video hoàn chỉnh</h3></div><button className="link-button" onClick={() => setActive("research")}>Mở workflow <Icon name="arrow" size={15}/></button></div>
      <div className="pipeline-grid">{pipeline.map((step, index) => <button key={step.id} className="pipeline-step" onClick={() => setActive(step.action)}><span className="step-index">{step.id}</span><span className="step-icon"><Icon name={step.icon}/></span><strong>{step.title}</strong><p>{step.text}</p>{index < pipeline.length - 1 && <span className="connector"><Icon name="arrow" size={15}/></span>}</button>)}</div>
    </section>
    <section className="panel span-4 brand-setup">
      <div className="section-heading"><div><span className="kicker">Brand memory</span><h3>Thiết lập dùng lại</h3></div><span className="completion">4/4</span></div>
      <label>Tên thương hiệu<input value={brand.name} onChange={(e) => setBrand({ ...brand, name: e.target.value })}/></label>
      <label>Ngách nội dung<input value={brand.niche} onChange={(e) => setBrand({ ...brand, niche: e.target.value })}/></label>
      <label>Khán giả<input value={brand.audience} onChange={(e) => setBrand({ ...brand, audience: e.target.value })}/></label>
      <label>Giọng thương hiệu<input value={brand.voice} onChange={(e) => setBrand({ ...brand, voice: e.target.value })}/></label>
      <button className="button primary wide" onClick={startPipeline}>Dùng cấu hình này</button>
    </section>
  </div>;
}

function Metric({ value, label, delta }) { return <div className="metric"><div><strong>{value}</strong><span>{label}</span></div><small>{delta}</small></div>; }

function Research({ brand, setBrand, trends, selectedTrend, setSelectedTrend, runResearch, researching, researchMode, writeScript, writing }) {
  return <div className="page-stack">
    <section className="page-intro"><div><span className="kicker">Bước 1 / 4</span><h2>Tìm tín hiệu đáng để kể lại</h2><p>Research không để sao chép. Nó giúp bạn nhìn thấy cấu trúc, nỗi đau và góc tiếp cận đang có lực kéo.</p></div><span className={`pill ${researchMode === "live" ? "success" : "neutral"}`}><span className="status-dot"/>{researchMode === "live" ? "Apify live" : "Demo data"}</span></section>
    <section className="search-panel"><label htmlFor="niche">Ngành hoặc chủ đề</label><div className="search-row"><div className="search-input"><Icon name="search"/><input id="niche" value={brand.niche} onChange={(e) => setBrand({ ...brand, niche: e.target.value })} placeholder="Ví dụ: bất động sản nghỉ dưỡng"/></div><button className="button primary" onClick={runResearch} disabled={researching}>{researching ? <><span className="spinner"/> Đang quét</> : "Quét nội dung"}</button></div><div className="filter-row"><span>Tiêu chí:</span><b>12 tháng gần nhất</b><b>≥ 3.000 views</b><b>Breakout ratio</b><b>Video ngắn</b></div></section>
    <div className="research-layout"><section className="trend-list"><div className="list-head"><h3>Kết quả nổi bật</h3><span>{trends.length} tín hiệu</span></div>{trends.map((trend, index) => <button key={trend.id} onClick={() => setSelectedTrend(trend)} className={`trend-card ${selectedTrend?.id === trend.id ? "selected" : ""}`}><span className="rank">0{index + 1}</span><div className="trend-content"><span className="trend-source">{trend.channel} · {trend.duration}</span><strong>{trend.title}</strong><p>“{trend.hook}”</p><div className="trend-meta"><span><b>{formatViews(trend.views)}</b> views</span><span><b>{trend.breakout}×</b> breakout</span><span>{trend.angle}</span></div></div><span className="select-ring"><Icon name="check" size={15}/></span></button>)}</section>
      <aside className="insight-panel"><span className="kicker">Phân tích nguồn</span><h3>{selectedTrend?.angle}</h3><div className="insight-score"><div className="score-ring"><strong>{Math.min(98, Math.round((selectedTrend?.breakout || 0) * 5.6))}</strong><span>/100</span></div><div><b>Tiềm năng chuyển thể</b><p>Hook có xung đột rõ, dễ gắn góc nhìn riêng và minh hoạ bằng visual proof.</p></div></div><div className="insight-block"><span>Cấu trúc nên học</span><ol><li>Nêu lỗi phổ biến trong 3 giây</li><li>Lật lại giả định bằng bằng chứng</li><li>Đưa một bước làm cụ thể</li></ol></div><div className="insight-block"><span>Không được sao chép</span><p>Câu chữ, ví dụ riêng, nhịp kể và CTA của nguồn.</p></div><button className="button primary wide" onClick={writeScript} disabled={writing}>{writing ? <><span className="spinner"/> Đang viết</> : <>Viết kịch bản từ góc này <Icon name="arrow" size={16}/></>}</button></aside>
    </div>
  </div>;
}

function ScriptEditor({ script, setScript, scriptLength, writeScript, writing, setActive }) {
  const estimated = Math.max(18, Math.round(scriptLength / 12));
  return <div className="page-stack"><section className="page-intro"><div><span className="kicker">Bước 2 / 4</span><h2>Biên tập trước khi sản xuất</h2><p>AI tạo bản nháp. Bạn giữ quyền quyết định góc nhìn, câu chữ và lời hứa của thương hiệu.</p></div><button className="button secondary" onClick={writeScript} disabled={writing}><Icon name="spark" size={17}/> Tạo phương án khác</button></section>
    <div className="editor-layout"><section className="script-editor"><div className="editor-toolbar"><span>Bản nháp 01</span><div><b>{scriptLength}</b> ký tự · <b>~{estimated}s</b></div></div><ScriptField label="Hook · 0–3s" value={script.hook} onChange={(value) => setScript({ ...script, hook: value })} tone="hook"/><ScriptField label="Nội dung · 3–48s" value={script.body} onChange={(value) => setScript({ ...script, body: value })} rows={9}/><ScriptField label="CTA · 48–55s" value={script.cta} onChange={(value) => setScript({ ...script, cta: value })} tone="cta"/><div className="editor-footer"><span><Icon name="check" size={16}/> Tự lưu trong trình duyệt</span><button className="button primary" onClick={() => setActive("production")}>Duyệt kịch bản <Icon name="arrow" size={16}/></button></div></section>
      <aside className="quality-panel"><span className="kicker">Script quality</span><h3>Kiểm tra trước khi duyệt</h3><Quality label="Hook vào thẳng vấn đề" value={92}/><Quality label="Chỉ có một ý chính" value={88}/><Quality label="Có ví dụ / bằng chứng" value={84}/><Quality label="CTA không ép bán" value={95}/><div className="quality-note"><Icon name="spark"/><p><strong>Gợi ý biên tập</strong>Thử thay “vấn đề” ở hook bằng một tình huống người xem gặp mỗi ngày để tăng tính nhận diện.</p></div><div className="guardrails"><span>Brand guardrails</span><p><Icon name="check" size={15}/> Không cam kết kết quả tuyệt đối</p><p><Icon name="check" size={15}/> Không sao chép nguồn research</p><p><Icon name="check" size={15}/> Ngôn ngữ tự nhiên, dễ đọc</p></div></aside>
    </div></div>;
}

function ScriptField({ label, value, onChange, rows = 3, tone = "" }) { return <label className={`script-field ${tone}`}><span>{label}</span><textarea rows={rows} value={value} onChange={(e) => onChange(e.target.value)}/></label>; }
function Quality({ label, value }) { return <div className="quality-row"><div><span>{label}</span><b>{value}%</b></div><div className="quality-track"><i style={{ width: `${value}%` }}/></div></div>; }

function Production({ styles, styleId, setStyleId, selectedStyle, videoMode, setVideoMode, script, brand, job, progress, startPipeline, downloadManifest }) {
  const stage = progress < 22 ? "Chuẩn bị project" : progress < 45 ? "Tạo avatar & giọng" : progress < 68 ? "Align subtitle" : progress < 91 ? "Dựng visual proof" : "QA bản render";
  return <div className="page-stack"><section className="page-intro"><div><span className="kicker">Bước 3–4 / 4</span><h2>Chọn ngôn ngữ hình ảnh</h2><p>Style quyết định nhịp cắt, caption, B-roll và cách mỗi luận điểm được chứng minh.</p></div>{job && <span className="pill success"><span className="status-dot"/> Job {job.jobId}</span>}</section>
    <div className="production-layout"><section className="production-controls"><div className="control-section"><div className="control-title"><span>01</span><div><h3>Hình thức video</h3><p>Giữ một giọng nói nhất quán trong toàn bộ video.</p></div></div><div className="segmented"><button className={videoMode === "avatar" ? "active" : ""} onClick={() => setVideoMode("avatar")}><Icon name="user"/> Avatar chính chủ</button><button className={videoMode === "noface" ? "active" : ""} onClick={() => setVideoMode("noface")}><Icon name="layers"/> No-face</button></div></div>
      <div className="control-section"><div className="control-title"><span>02</span><div><h3>Phong cách edit</h3><p>Preset là bộ quy tắc dựng, không chỉ là màu sắc.</p></div></div><div className="style-grid">{styles.map((style) => <button key={style.id} className={`style-card ${styleId === style.id ? "selected" : ""}`} onClick={() => setStyleId(style.id)}><div className="swatches">{style.palette.map((color) => <i key={color} style={{ background: color }}/>)}</div><strong>{style.name}</strong><span>{style.bestFor}</span><p>{style.description}</p><b className="style-check"><Icon name="check" size={14}/></b></button>)}</div></div>
      <div className="control-section"><div className="control-title"><span>03</span><div><h3>Nguyên tắc dựng</h3><p>Đã kế thừa từ pipeline thực chiến và skill Editorial Edit.</p></div></div><div className="rules-grid"><Rule title="Semantic cuts" text="Cắt theo nhịp ý nghĩa, không theo khoảng thời gian cố định."/><Rule title="Technical proof" text="Luận điểm kỹ thuật phải có chart, sơ đồ hoặc visual chứng minh."/><Rule title="Safe captions" text="Tối đa 2 dòng, theo đúng lời nói, không đè nhãn biểu đồ."/><Rule title="Zero flash" text="Kiểm tra mọi ranh giới scene, không để frame chớp ngoài ý muốn."/></div></div>
      <button className="button primary launch" onClick={startPipeline}><Icon name="bolt"/> Khởi chạy pipeline</button></section>
      <aside className="preview-panel"><div className="preview-head"><div><span className="kicker">Live preview</span><h3>{selectedStyle.name}</h3></div><span>9:16 · 1080p</span></div><div className={`video-preview style-${styleId}`}><div className="preview-safe"><span className="preview-label">{selectedStyle.name}</span><div className="preview-person"><Icon name={videoMode === "avatar" ? "user" : "layers"} size={46}/></div><strong>{script.hook}</strong><p>{script.body.slice(0, 86)}…</p><small>@{brand.name.toLowerCase().replace(/\s+/g, "")}</small></div></div>{job ? <div className="render-status"><div><span>{progress >= 100 ? "Bản demo đã sẵn sàng" : stage}</span><b>{progress}%</b></div><div className="render-track"><i style={{ width: `${progress}%` }}/></div><p>{progress >= 100 ? "Manifest đã qua kiểm tra cấu trúc. Render MP4 production chạy bằng engine local." : "Pipeline đang mô phỏng luồng production để không tiêu tốn API credit."}</p>{progress >= 100 && <button className="button secondary wide" onClick={downloadManifest}><Icon name="download" size={17}/> Tải production manifest</button>}</div> : <div className="preview-empty"><Icon name="clock"/><p>Chưa có job đang chạy</p><span>Bấm “Khởi chạy pipeline” để test toàn bộ luồng.</span></div>}</aside>
    </div></div>;
}

function Rule({ title, text }) { return <div className="rule"><Icon name="check" size={17}/><div><strong>{title}</strong><p>{text}</p></div></div>; }

function Library({ job, style, brand, downloadManifest }) {
  return <div className="page-stack"><section className="page-intro"><div><span className="kicker">Kho sản phẩm</span><h2>Mỗi video là một project có thể tái tạo</h2><p>Lưu nguồn research, kịch bản, style, manifest và báo cáo QA cùng nhau.</p></div></section><section className="library-card"><div className="library-thumb"><Icon name="play" size={30}/><span>9:16</span></div><div className="library-info"><span className="pill success"><span className="status-dot"/> Demo hoàn tất</span><h3>{job ? "Video mới từ BrandFlow" : "Video mẫu Editorial Proof"}</h3><p>{brand.niche} · {style.name} · Avatar</p><div><span><Icon name="clock" size={15}/> 00:55</span><span>1080 × 1920</span><span>QA 96%</span></div></div><div className="library-actions"><button className="icon-button" aria-label="Tải manifest" onClick={downloadManifest}><Icon name="download"/></button><button className="icon-button" aria-label="Mở chi tiết"><Icon name="external"/></button></div></section><section className="empty-library"><Icon name="library" size={28}/><h3>Project tiếp theo sẽ xuất hiện ở đây</h3><p>BrandFlow lưu đầy đủ ngữ cảnh để bạn sửa, render lại hoặc đổi style mà không phải bắt đầu từ đầu.</p></section></div>;
}
