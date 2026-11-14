from typing import List, Optional
from config import AuditConfig
from core.models import ProcurementLineItem, MarketBenchmark, AnomalyFinding, AgentDebateTurn

class AnomalyEngineTool:
    """
    Forensic mathematical engine that assesses price-gouging variance,
    incorporates multi-agent debate transcripts, and calculates public fiscal loss.
    """
    name: str = "anomaly_engine"
    description: str = "Computes statistical gouging indexes, risk tiers, and potential taxpayer loss based on agent consensus."

    @staticmethod
    def evaluate_item(
        item: ProcurementLineItem,
        benchmark: MarketBenchmark,
        consensus_price: Optional[float] = None,
        debate_transcript: Optional[List[AgentDebateTurn]] = None
    ) -> AnomalyFinding:
        quoted_unit = item.quoted_unit_price
        # Use consensus price if deliberated by the Multi-Agent Council
        fair_unit = consensus_price if consensus_price is not None else benchmark.fair_market_unit_price
        
        variance_unit = quoted_unit - fair_unit
        variance_total = variance_unit * item.quantity
        
        # Gouging Percentage formula: ((Quoted - Fair) / Fair) * 100
        gouging_pct = ((quoted_unit - fair_unit) / fair_unit) * 100 if fair_unit > 0 else 0.0
        
        # Risk Classification
        if gouging_pct > AuditConfig.CRITICAL_THRESHOLD_PERCENT:
            risk_level = "CRITICAL_RED_FLAG"
            audit_notes = (
                f"Severe anomaly: Quoted rate exceeds multi-agent consensus benchmark by {gouging_pct:.1f}%. "
                f"Potential budget siphoning or vendor collusive pricing detected."
            )
        elif gouging_pct > AuditConfig.WARNING_THRESHOLD_PERCENT:
            risk_level = "SUSPICIOUS_WARNING"
            audit_notes = (
                f"Moderate markup: Quoted rate is {gouging_pct:.1f}% above multi-agent consensus ceiling. "
                f"Requires detailed cost breakdown from supplier."
            )
        else:
            risk_level = "NORMAL"
            audit_notes = f"Compliant: Pricing is within statutory public procurement tolerance ({gouging_pct:+.1f}% vs consensus ceiling)."

        return AnomalyFinding(
            item_id=item.item_id,
            item_name=item.name,
            quantity=item.quantity,
            quoted_unit_price=quoted_unit,
            quoted_total_price=item.quoted_total_price,
            fair_market_unit_price=fair_unit,
            fair_market_total_price=fair_unit * item.quantity,
            variance_unit=variance_unit,
            variance_total=max(0.0, variance_total),
            gouging_percentage=gouging_pct,
            risk_level=risk_level,
            audit_notes=audit_notes,
            evidence_source=f"{benchmark.price_source} [Multi-Agent Consensus]",
            debate_transcript=debate_transcript or []
        )

    @staticmethod
    def calculate_overall_risk_score(findings: List[AnomalyFinding]) -> int:
        if not findings:
            return 0
            
        critical_count = sum(1 for f in findings if f.risk_level == "CRITICAL_RED_FLAG")
        warning_count = sum(1 for f in findings if f.risk_level == "SUSPICIOUS_WARNING")
        
        total_quoted = sum(f.quoted_total_price for f in findings)
        total_variance = sum(f.variance_total for f in findings)
        
        loss_ratio = (total_variance / total_quoted) if total_quoted > 0 else 0
        
        # Weighted score computation
        score = (critical_count * 25) + (warning_count * 10) + int(loss_ratio * 40)
        return min(100, max(0, score))
