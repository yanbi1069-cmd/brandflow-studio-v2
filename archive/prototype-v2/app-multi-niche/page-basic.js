"use client";

import { useMemo, useState } from "react";
import domainPacks from "@/config/domain-packs.json";
import contentFormats from "@/config/content-formats.json";
import editStyles from "@/config/edit-styles-v2.json";
import { recommendedStyleIds } from "@/lib/domain-engine";
import styles from "./studio.module.css";

const Icon = ({name}) => {
  const paths = {spark:<path d="m12 3-1.2 4.1A5.5 5.5 0 0 1 7.1 11L3 12l4.1 1.2a5.5 5.5 0 0 1 3.7 3.7L12 21l1.2-4.1a5.5 5.5 0 0 1 3.7-3.7L21 12l-4.1-1.2a5.5 5.5 0 0 1-3.7-3.7Z"/>,check:<path d="m5 12 4 4L19 6"/>,arrow:<path d="m9 18 6-6-6-6"/>,download:<><path d="M12 3v12m0 0 4-4m-4 4-4-4"/><path d="M5 20h14"/></>};
  return <svg aria-hidden="true" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>;
};

export default function MultiNicheStudio() {
  const [domainId,setDomainId]=useState("finance");
  const [formatId,setFormatId]=useState("evidence-explainer");
  const domain=useMemo(()=>domainPacks.find(x=>x.id===domainId)||domainPacks[0],[domainId]);
  const format=useMemo(()=>contentFormats.find(x=>x.id===formatId)||contentFormats[0],[formatId]);
  const recommended=useMemo(()=>recommendedStyleIds(domainId,formatId),[domainId,formatId]);
  const [brand,setBrand]=useState({name:"SFI Academy",niche:domain.niche,audience:domain.audience,voice:domain.voice});
  const [styleId,setStyleId]=useState("editorial-proof");
  const [videoMode,setVideoMode]=useState("avatar");
  const [script,setScript]=useState({hook:"Nếu nội dung của bạn giống mọi người, có thể vấn đề nằm ở cách bạn chứng minh.",body:"Chọn một ngành và format để BrandFlow tạo kịch bản phù hợp với khách hàng, loại bằng chứng và ràng buộc của ngành đó.",cta:"Lưu lại nếu bạn muốn biến chuyên môn thành một hệ thống nội dung."});
  const [busy,setBusy]=useState(false);
  const [job,setJob]=useState(null);
  const [notice,setNotice]=useState("Demo mode không gọi API trả phí.");
  const selectedStyle=editStyles.find(x=>x.id===styleId)||editStyles[0];

  function chooseDomain(id) {
    const next=domainPacks.find(x=>x.id===id)||domainPacks[0];
    setDomainId(id); setBrand(prev=>({...prev,niche:next.niche,audience:next.audience,voice:next.voice})); setStyleId(next.defaultStyle);
  }

  async function writeScript() {
    setBusy(true); setNotice("");
    try { const response=await fetch("/api/multi-niche/script",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({domainId,formatId,brandName:brand.name,...brand})}); const data=await response.json(); if(!response.ok) throw new Error(data.error); setScript(data); setNotice(data.sourceMode==="live"?`Đã tạo bằng ${data.model}.`:"Đã tạo bằng engine demo, không tiêu tốn credit."); }
    catch(error){setNotice(error.message||"Không thể tạo kịch bản.");} finally{setBusy(false);}
  }

  async function buildManifest() {
    setBusy(true); setNotice("");
    try { const response=await fetch("/api/multi-niche/pipeline",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({domainId,formatId,brand,script,videoMode,editStyle:selectedStyle})}); const data=await response.json(); setJob(data); setNotice("Production manifest v2 đã sẵn sàng. Các checkpoint duyệt vẫn đang khóa."); }
    catch(error){setNotice(error.message||"Không thể tạo manifest.");} finally{setBusy(false);}
  }

  function downloadManifest(){if(!job?.manifest)return;const blob=new Blob([JSON.stringify(job.manifest,null,2)],{type:"application/json"});const url=URL.createObjectURL(blob);const link=document.createElement("a");link.href=url;link.download=`${job.jobId.toLowerCase()}-manifest.json`;link.click();URL.revokeObjectURL(url);}

  return <main className={styles.shell}>
    <header className={styles.header}><div className={styles.logo}><span><Icon name="spark"/></span>BrandFlow <b>Multi-Niche</b></div><div className={styles.mode}><i/> Demo an toàn</div></header>
    <section className={styles.hero}><div><p>AI VIDEO OPERATING SYSTEM</p><h1>Một agent. Nhiều ngành.<br/><em>Đúng logic từng ngách.</em></h1><span>Finance là chuẩn tham chiếu; domain pack quyết định research, bằng chứng, compliance và phong cách dựng cho từng ngành.</span></div><div className={styles.summary}><small>CẤU HÌNH HIỆN TẠI</small><strong>{domain.name}</strong><span>{format.name} · {selectedStyle.name}</span><div>{domain.proofTypes.map(item=><b key={item}>{item}</b>)}</div></div></section>
    {notice&&<div className={styles.notice} role="status"><Icon name="check"/>{notice}</div>}
    <div className={styles.grid}>
      <section className={styles.panel}><div className={styles.title}><span>01</span><div><h2>Chọn domain pack</h2><p>Mỗi ngành có audience, proof và rule an toàn riêng.</p></div></div><div className={styles.domainGrid}>{domainPacks.map(item=><button key={item.id} aria-pressed={domainId===item.id} className={domainId===item.id?styles.selected:""} onClick={()=>chooseDomain(item.id)}><strong>{item.name}</strong><span>{item.defaultStyle}</span></button>)}</div><div className={styles.formGrid}><label>Tên thương hiệu<input value={brand.name} onChange={e=>setBrand({...brand,name:e.target.value})}/></label><label>Ngách cụ thể<input value={brand.niche} onChange={e=>setBrand({...brand,niche:e.target.value})}/></label><label>Khán giả<textarea rows="2" value={brand.audience} onChange={e=>setBrand({...brand,audience:e.target.value})}/></label><label>Giọng thương hiệu<textarea rows="2" value={brand.voice} onChange={e=>setBrand({...brand,voice:e.target.value})}/></label></div><div className={styles.guardrails}><strong>Ràng buộc theo ngành</strong>{domain.compliance.map(item=><span key={item}><Icon name="check"/>{item}</span>)}{domain.disclaimer&&<p>{domain.disclaimer}</p>}</div></section>
      <section className={styles.panel}><div className={styles.title}><span>02</span><div><h2>Chọn format nội dung</h2><p>Chọn cấu trúc kể chuyện trước khi viết câu chữ.</p></div></div><div className={styles.formatList}>{contentFormats.map(item=><button key={item.id} aria-pressed={formatId===item.id} className={formatId===item.id?styles.selected:""} onClick={()=>setFormatId(item.id)}><span><strong>{item.name}</strong><small>{item.bestFor}</small></span><Icon name="arrow"/></button>)}</div><div className={styles.structure}>{format.structure.map((item,index)=><span key={item}><b>{index+1}</b>{item}</span>)}</div><button className={styles.primary} onClick={writeScript} disabled={busy}>{busy?"Đang xử lý...":"Tạo kịch bản theo ngách"}</button></section>
      <section className={`${styles.panel} ${styles.wide}`}><div className={styles.title}><span>03</span><div><h2>Kịch bản & creative brief</h2><p>Chỉnh trực tiếp trước checkpoint duyệt.</p></div></div><div className={styles.scriptGrid}><label>Hook<textarea rows="2" value={script.hook} onChange={e=>setScript({...script,hook:e.target.value})}/></label><label>Body<textarea rows="6" value={script.body} onChange={e=>setScript({...script,body:e.target.value})}/></label><label>CTA<textarea rows="2" value={script.cta} onChange={e=>setScript({...script,cta:e.target.value})}/></label></div></section>
      <section className={`${styles.panel} ${styles.wide}`}><div className={styles.title}><span>04</span><div><h2>Chọn production route & style</h2><p>10 preset edit được chuẩn hóa từ Finance Editorial và các pattern chọn lọc của mkt-skills.</p></div></div><div className={styles.routes}><button className={videoMode==="avatar"?styles.selected:""} onClick={()=>setVideoMode("avatar")}><strong>AI Avatar</strong><span>HeyGen + voice alignment</span></button><button className={videoMode==="noface"?styles.selected:""} onClick={()=>setVideoMode("noface")}><strong>No-face</strong><span>Voice + visual proof</span></button><button className={videoMode==="upload"?styles.selected:""} onClick={()=>setVideoMode("upload")}><strong>Raw footage</strong><span>Jump-cut + captions</span></button></div><div className={styles.styleGrid}>{editStyles.map(item=><button key={item.id} aria-pressed={styleId===item.id} className={styleId===item.id?styles.selected:""} onClick={()=>setStyleId(item.id)}><div>{item.palette.map(color=><i key={color} style={{background:color}}/>)}</div><strong>{item.name}{recommended.includes(item.id)&&<small>Đề xuất</small>}</strong><span>{item.bestFor}</span><p>{item.description}</p></button>)}</div><div className={styles.actions}><button className={styles.primary} onClick={buildManifest} disabled={busy}>Tạo production manifest</button><button className={styles.secondary} onClick={downloadManifest} disabled={!job}><Icon name="download"/> Tải manifest</button></div>{job&&<div className={styles.job}><Icon name="check"/><div><strong>{job.jobId} · Manifest v2.0</strong><span>Research → Script → nguồn video → edit → QA → Skip/Publish</span></div></div>}</section>
    </div>
  </main>;
}
