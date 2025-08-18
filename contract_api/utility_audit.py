import google.generativeai as genai
from django.conf import settings
from .models import AuditFinding, DocumentPage
import uuid
import json

# Configure Gemini client
genai.configure(api_key=settings.GEMINI_API_KEY)

AUDIT_PROMPT = """
You are a contract risk auditor. Analyze the following contract text and return a JSON list of risky clauses.

For each finding, return:
- finding_type: short label (e.g., "Auto-renewal", "Unlimited liability")
- title: human-readable title
- description: why this is risky
- severity: one of [low, medium, high, critical]
- risk_score: float 0-10
- evidence_text: exact span of text that triggered this
- page_number: page number where evidence occurs
- char_start: character start position in that page
- char_end: character end position in that page
- recommendation: how to mitigate
- compliance_impact: potential legal/operational impact

Output only valid JSON array of objects. Do not include explanations outside JSON.
"""

def run_audit(document):
    # Gather all pages
    pages = DocumentPage.objects.filter(document=document).order_by("page_number")
    all_text = "\n\n".join([f"[PAGE {p.page_number}]\n{p.text}" for p in pages if p.text.strip()])

    if not all_text.strip():
        return []

    prompt = f"""{AUDIT_PROMPT}

Contract content:
{all_text}
"""

    # Use Gemini
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )

    findings = []
    try:
        parsed = json.loads(response.text)

        for f in parsed:
            page_number = f.get("page_number", 1)
            evidence_text = f.get("evidence_text", "")
            char_start = f.get("char_start", 0)
            char_end = f.get("char_end", len(evidence_text))

            finding = AuditFinding(
                id=uuid.uuid4(),
                document=document,
                finding_type=f.get("finding_type", ""),
                title=f.get("title", ""),
                description=f.get("description", ""),
                severity=f.get("severity", "medium"),
                risk_score=float(f.get("risk_score", 5)),
                evidence_text=evidence_text,
                page_number=page_number,
                char_start=char_start,
                char_end=char_end,
                recommendation=f.get("recommendation", ""),
                compliance_impact=f.get("compliance_impact", ""),
                detection_model="gemini-1.5-flash",
            )
            finding.save()
            findings.append(finding)

    except Exception as e:
        print(f"Error parsing audit response: {e}")

    return findings
