"use client";

import { useEffect, useMemo, useState } from "react";
import styles from "./page.module.css";

const demoVideoUrl = process.env.NEXT_PUBLIC_DEMO_VIDEO_URL || "/brandflow-demo.mp4";
const posthogToken = process.env.NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN;
const posthogHost = process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://us.i.posthog.com";

function attribution() {
  if (typeof window === "undefined") return {};
  const params = new URLSearchParams(window.location.search);
  return { utm_source: params.get("utm_source") || "direct", utm_medium: params.get("utm_medium") || "none", utm_campaign: params.get("utm_campaign") || "none" };
}

function getDistinctId() {
  const key = "brandflow_distinct_id";
  let distinctId = window.localStorage.getItem(key);
  if (!distinctId) {
    distinctId = window.crypto?.randomUUID?.() || `brandflow-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    window.localStorage.setItem(key, distinctId);
  }
  return distinctId;
}

function capture(event, properties = {}, distinctId) {
  if (!posthogToken || typeof window === "undefined") return Promise.resolve({ ok: false });
  const endpoint = `${posthogHost.replace(/\/$/, "")}/i/v0/e/`;
  const payload = JSON.stringify({ api_key: posthogToken, event, distinct_id: distinctId || getDistinctId(), properties: { ...attribution(), ...properties, $current_url: window.location.href } });
  if (navigator.sendBeacon) {
    return Promise.resolve({ ok: navigator.sendBeacon(endpoint, new Blob([payload], { type: "application/json" })) });
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);
  return fetch(endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: payload, keepalive: true, signal: controller.signal })
    .finally(() => clearTimeout(timeout));
}

export default function Home() {
  const [status, setStatus] = useState("idle");
  const [message, setMessage] = useState("");
  const utm = useMemo(attribution, []);
  useEffect(() => {
    const visitKey = `brandflow_distribution_visit:${window.location.pathname}${window.location.search}`;
    if (window.sessionStorage.getItem(visitKey)) return;
    window.sessionStorage.setItem(visitKey, "sent");
    capture("distribution_visit", { acquisition_channel: utm.utm_source });
  }, [utm]);
  async function submit(event) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setStatus("loading"); setMessage("");
    try {
      if (String(form.get("website") || "").trim()) return;
      const email = String(form.get("email") || "").trim().toLowerCase();
      const response = await capture("sign_up_completed", { acquisition_channel: utm.utm_source, name: String(form.get("name") || "").trim(), email, goal: String(form.get("goal") || "").trim() }, email);
      if (!response?.ok) throw new Error("PostHog chưa thể ghi nhận đăng ký.");
      formElement.reset();
      setStatus("success"); setMessage("Đăng ký đã được ghi nhận. Mình sẽ gửi thông tin trải nghiệm sớm nhất.");
    } catch (error) { setStatus("error"); setMessage(error.message || "Có lỗi xảy ra. Vui lòng thử lại."); }
  }
  return <main className={styles.page}>
    <header className={styles.header}><a className={styles.brand} href="#top" aria-label="BrandFlow Studio trang chủ"><span aria-hidden="true">B</span> BrandFlow Studio</a><a className={styles.headerLink} href="#dang-ky">Đăng ký trải nghiệm</a></header>
    <section className={styles.hero} id="top"><div className={styles.heroCopy}><p className={styles.eyebrow}>AI VIDEO WORKFLOW CHO CHUYÊN GIA &amp; SME</p><h1>Biến insight thành video thương hiệu <em>có thể xuất bản.</em></h1><p className={styles.lead}>BrandFlow kết nối research, kịch bản, video nguồn, hậu kỳ dọc và QA — để bạn xuất bản đều đặn mà không bắt đầu lại từ số 0.</p><div className={styles.actions}><a className={styles.primaryButton} href="#dang-ky" onClick={() => capture("cta_clicked", { placement: "hero" })}>Nhận quyền trải nghiệm</a><a className={styles.textButton} href="#demo">Xem demo 90 giây ↓</a></div><p className={styles.note}>Đang mở nhóm trải nghiệm đầu tiên. Không cần thẻ thanh toán.</p></div><div className={styles.flowCard} aria-label="Quy trình BrandFlow"><p>BRANDFLOW PIPELINE</p>{[["01","Research","Tìm tín hiệu và góc nội dung"],["02","Script","Duyệt thông điệp trước khi quay"],["03","Edit","Video dọc, caption và QA"]].map(([n,title,description]) => <div className={styles.flowStep} key={n}><b>{n}</b><div><strong>{title}</strong><span>{description}</span></div></div>)}</div></section>
    <section className={styles.demo} id="demo"><div><p className={styles.eyebrow}>XEM SẢN PHẨM VẬN HÀNH</p><h2>Một workflow rõ ràng, từ ý tưởng đến file video.</h2></div><div className={styles.videoFrame}>{demoVideoUrl ? <video controls preload="metadata" aria-label="Video demo BrandFlow Studio"><source src={demoVideoUrl} />Trình duyệt không hỗ trợ video.</video> : <div className={styles.videoPlaceholder}><span>VIDEO DEMO</span><strong>Video 90–120 giây sẽ hiển thị tại đây</strong><p>Thêm <code>NEXT_PUBLIC_DEMO_VIDEO_URL</code> để phát video public.</p></div>}</div></section>
    <section className={styles.valueGrid}><article><span>01</span><h3>Bắt đầu từ dữ liệu</h3><p>Research theo thị trường, niche hoặc kênh đối thủ thay vì đoán chủ đề.</p></article><article><span>02</span><h3>Kiểm soát thông điệp</h3><p>Duyệt kịch bản trước khi tạo video để nội dung vẫn đúng giọng thương hiệu.</p></article><article><span>03</span><h3>Xuất bản nhanh hơn</h3><p>Caption, B-roll, định dạng 9:16 và QA nằm trong một luồng thực thi.</p></article></section>
    <section className={styles.signup} id="dang-ky"><div className={styles.signupCopy}><p className={styles.eyebrow}>NHÓM TRẢI NGHIỆM ĐẦU TIÊN</p><h2>Bạn muốn biến chủ đề nào thành video đầu tiên?</h2><p>Thông tin đăng ký được lưu trong PostHog để đo lường danh sách trải nghiệm và liên hệ về BrandFlow.</p></div><form className={styles.form} onSubmit={submit}><label>Họ và tên<input name="name" autoComplete="name" required /></label><label>Email công việc<input name="email" type="email" autoComplete="email" required /></label><label>Bạn muốn làm video về gì? <span>(không bắt buộc)</span><textarea name="goal" rows="3" placeholder="Ví dụ: chia sẻ kiến thức tài chính cá nhân" /></label><input className={styles.honeypot} name="website" tabIndex="-1" autoComplete="off" aria-hidden="true" /><button className={styles.submitButton} type="submit" disabled={status === "loading"}>{status === "loading" ? "Đang gửi…" : "Đăng ký trải nghiệm"}</button><p className={`${styles.feedback} ${status === "error" ? styles.error : ""}`} role="status" aria-live="polite">{message}</p></form></section>
    <footer className={styles.footer}><span>© {new Date().getFullYear()} BrandFlow Studio</span><a href="/multi-niche">Mở Studio</a></footer>
  </main>;
}
