import { getContentFormat, getDomainPack, recommendedStyleIds } from "@/lib/domain-engine";

export async function POST(request) {
  const input = await request.json();
  if (!input.approvals?.researchApproved || !input.approvals?.scriptApproved) {
    return Response.json({ error: "Cần duyệt nguồn research và kịch bản trước khi tạo manifest." }, { status: 409 });
  }
  const domain = getDomainPack(input.domainId);
  const format = getContentFormat(input.formatId);
  const jobId = `BF2-${Date.now().toString(36).toUpperCase()}`;
  return Response.json({
    jobId,
    status:"ready",
    mode:process.env.HEYGEN_API_KEY ? "production-ready" : "demo",
    manifest:{
      schemaVersion:"2.0",
      createdAt:new Date().toISOString(),
      project:{id:jobId,brand:input.brand,niche:input.brand?.niche || domain.niche,domainPackId:domain.id,contentFormatId:format.id,format:"vertical-9:16",targetDurationSec:55},
      domainPack:domain,
      contentFormat:format,
      source:input.source || null,
      script:input.script,
      production:{videoMode:input.videoMode || "avatar",editStyle:input.editStyle,recommendedStyleIds:recommendedStyleIds(domain.id,format.id)},
      approvals:{researchApproved:true,scriptApproved:true,externalCostConfirmed:false,finalApproved:false,publishingConfirmed:false},
      qa:{captionSafeArea:true,maxCaptionLines:2,requireNoFlashFrames:true,requireVoiceAlignment:true,requireSourceTraceability:true,requireFullWatch:true,maxDurationSec:60},
      distribution:{defaultAction:"skip"}
    }
  });
}
