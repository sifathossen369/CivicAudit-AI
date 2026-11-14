import hashlib
from typing import List, Dict, Any
from datetime import datetime
from config import AuditConfig
from core.models import AnomalyFinding, AuditDossier
from core.tools.anomaly_engine import AnomalyEngineTool

class DossierGeneratorTool:
    """
    Synthesizes audit findings into an official oversight memorandum and audit dossier.
    """
    name: str = "dossier_generator"
    description: str = "Generates formalized forensic audit reports, executive memorandums, and compliance advisories."

    @staticmethod
    def compile_dossier(
        tender_id: str,
        title: str,
        procuring_entity: str,
        findings: List[AnomalyFinding]
    ) -> AuditDossier:
        total_quoted = sum(f.quoted_total_price for f in findings)
        total_fair = sum(f.fair_market_total_price for f in findings)
        taxpayer_loss = sum(f.variance_total for f in findings)
        
        overall_gouging = ((total_quoted - total_fair) / total_fair * 100) if total_fair > 0 else 0.0
        risk_score = AnomalyEngineTool.calculate_overall_risk_score(findings)
        
        if risk_score >= 70:
            risk_tier = "CRITICAL / HIGH FRAUD RISK"
        elif risk_score >= 40:
            risk_tier = "ELEVATED CONCERN"
        else:
            risk_tier = "ACCEPTABLE / LOW RISK"

        # Generate automated statutory notices
        violations = []
        if risk_score > 50:
            violations.append("Violation of Public Procurement Fair Market Competition Directives.")
            violations.append("Failure of Due Diligence in Independent Price Estimate (IPE).")
        if any(f.gouging_percentage > 100 for f in findings):
            violations.append("Possible Offense under Section 409/420 - Criminal Breach of Public Trust via Bid Siphoning.")

        # Recommendations
        actions = [
            "Halt contract execution pending independent Technical Evaluation Committee (TEC) review.",
            "Issue formal Request for Explanation (RFE) to primary bidder regarding flagged unit line items.",
            "Re-benchmark Bill of Quantities (BOQ) with National Central Procurement Authority catalog.",
            "Refer procurement dossier to Municipal Anti-Corruption Oversight Bureau."
        ]

        summary = (
            f"The forensic audit of tender '{title}' (ID: {tender_id}) conducted by CivicAudit AI reveals "
            f"an overall price inflation index of {overall_gouging:.1f}%. Out of {len(findings)} audited line-items, "
            f"{sum(1 for f in findings if f.risk_level == 'CRITICAL_RED_FLAG')} items were flagged as CRITICAL PRICE GOUGING. "
            f"The total potential loss to public funds is estimated at {AuditConfig.DEFAULT_CURRENCY}{taxpayer_loss:,.2f}."
        )

        return AuditDossier(
            tender_id=tender_id,
            title=title,
            procuring_entity=procuring_entity,
            submission_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            total_quoted_budget=total_quoted,
            fair_market_estimated_budget=total_fair,
            potential_taxpayer_loss=taxpayer_loss,
            overall_gouging_index=overall_gouging,
            risk_score=risk_score,
            risk_tier=risk_tier,
            findings=findings,
            executive_summary=summary,
            legal_statutory_violations=violations,
            immediate_actions_recommended=actions
        )

    @staticmethod
    def render_markdown(dossier: AuditDossier) -> str:
        curr = AuditConfig.DEFAULT_CURRENCY
        overall_sign = "+" if dossier.overall_gouging_index > 0 else ""
        
        # Calculate genuine SHA-256 integrity hash across findings and totals
        hash_payload = (
            f"{dossier.tender_id}|{dossier.total_quoted_budget:.2f}|"
            f"{dossier.fair_market_estimated_budget:.2f}|{len(dossier.findings)}|"
            f"{dossier.submission_date}"
        )
        forensic_sha256 = hashlib.sha256(hash_payload.encode("utf-8")).hexdigest()

        md = f"""# 🏛️ FORENSIC AUDIT DOSSIER
**CIVICAUDIT AI - SPECIAL INVESTIGATION UNIT**
*Report Reference: AUDIT-{dossier.tender_id} | Date: {dossier.submission_date}*

---

### 1. Procurement Metadata
- **Tender Reference:** `{dossier.tender_id}`
- **Title:** {dossier.title}
- **Procuring Authority:** {dossier.procuring_entity}
- **Integrity Assessment:** **{dossier.risk_tier} (Score: {dossier.risk_score}/100)**

---

### 2. Executive Financial Summary
| Metric | Value |
| :--- | :--- |
| **Total Quoted Bid Amount** | **{curr}{dossier.total_quoted_budget:,.2f}** |
| **Estimated Fair Market Value** | **{curr}{dossier.fair_market_estimated_budget:,.2f}** |
| **Taxpayer Exposure / Fiscal Drain** | **⚠️ {curr}{dossier.potential_taxpayer_loss:,.2f}** |
| **Aggregate Gouging Percentage** | **{overall_sign}{dossier.overall_gouging_index:.1f}%** |

**Forensic Finding:**
> {dossier.executive_summary}

---

### 3. Detailed Line-Item Audit & Discrepancy Matrix
| Item ID | Description | Qty | Quoted Unit | Market Fair | Variance / Loss | Gouging % | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
        for f in dossier.findings:
            flag_icon = "🔴 CRITICAL" if f.risk_level == "CRITICAL_RED_FLAG" else ("🟡 WARNING" if f.risk_level == "SUSPICIOUS_WARNING" else "🟢 NORMAL")
            g_sign = "+" if f.gouging_percentage > 0 else ""
            md += f"| `{f.item_id}` | {f.item_name} | {f.quantity} | {curr}{f.quoted_unit_price:,.2f} | {curr}{f.fair_market_unit_price:,.2f} | {curr}{f.variance_total:,.2f} | **{g_sign}{f.gouging_percentage:.1f}%** | {flag_icon} |\n"

        md += f"""
---

### 4. Statutory Violations & Compliance Red Flags
"""
        for v in dossier.legal_statutory_violations:
            md += f"- ❌ **{v}**\n"

        md += f"""
### 5. Immediate Remedial Actions Required
"""
        for a in dossier.immediate_actions_recommended:
            md += f"1. {a}\n"

        md += f"""
---
*Generated by CivicAudit Autonomous Forensic Engine v{AuditConfig.VERSION}*  
*Timestamp: {datetime.now().isoformat()} | SHA-256 Audit Verification Hash: `{forensic_sha256}`*
"""
        return md
