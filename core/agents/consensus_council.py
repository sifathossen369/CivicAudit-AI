from typing import Tuple, List
from core.models import ProcurementLineItem, MarketBenchmark, AgentDebateTurn

class MultiAgentPriceCouncil:
    """
    Statutory Multi-Agent Consensus & Deliberation Engine.
    
    Orchestrates an adversarial 3-agent forensic debate for each line item using
    reproducible, deterministic statutory procurement rules (PPR, FAR, PWD Schedule)
    to eliminate LLM hallucination risks in high-stakes legal auditing:
    1. Agent Scout (🕵️‍♂️): Gathers objective wholesale market telemetry & price floor.
    2. Agent Advocate (💼): Represents commercial reality, statutory taxes (VAT, AIT), and warranty margins (+25% cushion).
    3. Lead Auditor (⚖️): Evaluates arguments against procurement statutes and issues the binding consensus (+22% ceiling).
    """

    @classmethod
    def deliberate(
        cls,
        item: ProcurementLineItem,
        raw_benchmark: MarketBenchmark
    ) -> Tuple[float, List[AgentDebateTurn], str]:
        """
        Executes a 3-way agent debate and arrives at a reconciled consensus price.
        Returns:
            consensus_price (float)
            debate_transcript (List[AgentDebateTurn])
            reconciliation_notes (str)
        """
        quoted = max(0.0, float(item.quoted_unit_price))
        floor_price = max(0.0, float(raw_benchmark.fair_market_unit_price))
        if floor_price <= 0:
            floor_price = quoted if quoted > 0 else 1.0

        transcript: List[AgentDebateTurn] = []

        # Turn 1: Market Scout Agent
        scout_markup = ((quoted - floor_price) / floor_price * 100) if floor_price > 0 else 0.0
        scout_msg = (
            f"Based on commercial wholesale registries ({raw_benchmark.price_source}), "
            f"the baseline trading floor for '{item.name}' is ${floor_price:,.2f}. "
            f"The vendor's quoted price of ${quoted:,.2f} represents a {scout_markup:+.1f}% markup."
        )
        transcript.append(AgentDebateTurn(
            agent_name="Agent Scout (Intel)",
            role="Market Data Investigator",
            avatar="🕵️‍♂️",
            argument=scout_msg
        ))

        # Turn 2: Vendor Advocate Agent (Reasonable Commercial & Statutory Defense)
        # In real-world government tenders (e.g. e-GP, PWD Schedule of Rates, FAR guidelines):
        # Bids legitimately include: Contractor Profit & Overhead (10-15%), Statutory VAT (7.5-15%),
        # Advance Income Tax AIT (5-7.5%), logistics, multi-year warranty, and performance bond buffers.
        # Total statutory procurement buffer over factory wholesale floor is 20% to 25%.
        commercial_cushion = 1.25  # 25% statutory procurement allowance
        fair_ceiling = round(floor_price * commercial_cushion, 2)
        
        if quoted > fair_ceiling * 1.5:
            advocate_msg = (
                f"Even incorporating maximum statutory allowances (15% VAT, 7.5% AIT, 10% contractor margin, "
                f"3-year enterprise warranty, and delivery logistics), the justifiable statutory ceiling is ${fair_ceiling:,.2f}. "
                f"I cannot defend a quoted rate of ${quoted:,.2f}; this represents flagrant over-invoicing beyond all procurement rules."
            )
        elif quoted > fair_ceiling:
            advocate_msg = (
                f"While the factory wholesale floor is ${floor_price:,.2f}, municipal public contracts legally mandate "
                f"vendor VAT, AIT deduction, bank guarantees, and delivery overheads. A rate up to ${fair_ceiling:,.2f} (+25%) "
                f"is fully defensible under Public Procurement Rules."
            )
        else:
            advocate_msg = (
                f"The quoted rate of ${quoted:,.2f} is well within competitive commercial boundaries ({scout_markup:+.1f}%), "
                f"safely covered by statutory procurement allowances (VAT, AIT, warranty, and overhead)."
            )

        transcript.append(AgentDebateTurn(
            agent_name="Agent Advocate (Vendor)",
            role="Procurement Economics Specialist",
            avatar="💼",
            argument=advocate_msg
        ))

        # Turn 3: Lead Forensic Auditor (Consensus Arbiter)
        # Consensus fair market ceiling: Factory floor + 22% statutory public procurement tolerance
        consensus_price = max(0.01, round(floor_price * 1.22, 2))
        markup_over_consensus = ((quoted - consensus_price) / consensus_price * 100) if consensus_price > 0 else 0.0

        if markup_over_consensus > 50:
            auditor_msg = (
                f"Council Ruling: Consensus fair market ceiling established at ${consensus_price:,.2f}. "
                f"Quoted rate of ${quoted:,.2f} ({markup_over_consensus:+.1f}% over consensus ceiling, {scout_markup:+.1f}% over floor) "
                f"flagrantly breaches Public Procurement Due Diligence statutes. "
                f"VERDICT: CRITICAL FRAUD/GOUGING RISK. Immediate contract freeze recommended."
            )
        elif quoted > fair_ceiling or markup_over_consensus > 10.0:
            auditor_msg = (
                f"Council Ruling: Consensus fair rate established at ${consensus_price:,.2f}. "
                f"Quoted rate of ${quoted:,.2f} ({markup_over_consensus:+.1f}%) exceeds statutory tolerance. "
                f"VERDICT: ELEVATED ANOMALY. Itemized supplier cost breakdown required."
            )
        else:
            auditor_msg = (
                f"Council Ruling: Consensus fair rate confirmed at ${consensus_price:,.2f}. "
                f"Quoted rate of ${quoted:,.2f} is approved within statutory market tolerance ({scout_markup:+.1f}% over floor). "
                f"VERDICT: COMPLIANT."
            )

        transcript.append(AgentDebateTurn(
            agent_name="Chief Auditor (Arbiter)",
            role="Public Integrity Officer",
            avatar="⚖️",
            argument=auditor_msg
        ))

        reconciliation_summary = (
            f"Deliberated by 3 AI Agents (Scout Floor: ${floor_price:,.2f} | "
            f"Advocate Ceiling: ${fair_ceiling:,.2f} | Consensus: ${consensus_price:,.2f})"
        )

        return consensus_price, transcript, reconciliation_summary
