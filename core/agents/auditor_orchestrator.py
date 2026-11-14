import time
import logging
from typing import List, Dict, Any, Callable, Optional
from core.models import ProcurementLineItem, AnomalyFinding, AuditDossier
from core.tools.procurement_parser import ProcurementParserTool
from core.tools.market_verifier import MarketVerifierTool
from core.tools.anomaly_engine import AnomalyEngineTool
from core.tools.dossier_generator import DossierGeneratorTool
from core.agents.consensus_council import MultiAgentPriceCouncil

logger = logging.getLogger("CivicAudit.Orchestrator")

class CivicAuditOrchestrator:
    """
    Lead Forensic Agent Orchestrator.
    Manages autonomous multi-step investigation, multi-agent price debate councils,
    real-time live web inquiries, state reflection, and dossier synthesis.
    (Operates with Zero Cached Prices to uphold legal, fresh evidentiary standards).
    """
    def __init__(self, step_callback: Optional[Callable[[str, str, Any], None]] = None):
        self.step_callback = step_callback or (lambda phase, msg, data=None: None)
        self.parser = ProcurementParserTool()
        self.verifier = MarketVerifierTool()
        self.anomaly_engine = AnomalyEngineTool()
        self.dossier_generator = DossierGeneratorTool()

    def log(self, phase: str, message: str, data: Any = None):
        logger.info(f"[{phase}] {message}")
        self.step_callback(phase, message, data)

    def audit_tender(
        self,
        tender_id: str,
        title: str,
        procuring_entity: str,
        tender_source_data: Dict[str, Any]
    ) -> AuditDossier:
        """
        Executes the autonomous forensic audit pipeline with Multi-Agent Price Consensus
        and 100% fresh, contemporaneous live web market evaluations.
        """
        self.log("INIT", f"Initializing CivicAudit Special Investigation for Tender #{tender_id}")
        time.sleep(0.1)

        # STAGE 1: INGESTION & DECOMPOSITION
        self.log("STAGE_1", "Parsing Bill of Quantities (BOQ) and extracting line-items...")
        if "items" in tender_source_data:
            line_items = self.parser.parse_from_json(tender_source_data)
        else:
            raw_text = tender_source_data.get("raw_text", "")
            line_items = self.parser.parse_from_text(raw_text)

        self.log("STAGE_1", f"Successfully extracted {len(line_items)} procurement line items.", line_items)
        time.sleep(0.1)

        # STAGE 2: MULTI-AGENT MARKET INTELLIGENCE & DEBATE
        self.log("STAGE_2", "Convening Multi-Agent Price Deliberation Council...")
        findings: List[AnomalyFinding] = []

        for idx, item in enumerate(line_items, 1):
            self.log(
                "STAGE_2",
                f"[{idx}/{len(line_items)}] Conducting Fresh Live Inquiry on '{item.name}' (Quoted: ${item.quoted_unit_price:,.2f})..."
            )
            
            # Step A: Fresh real-time benchmark inquiry with item name, spec, and sanity reference
            raw_benchmark = self.verifier.query_benchmark(item.name, item.specification, item.quoted_unit_price)
            
            # Step B: Convene 3-Agent Council (Scout vs Advocate vs Arbiter)
            consensus_price, debate_transcript, summary = MultiAgentPriceCouncil.deliberate(item, raw_benchmark)
            
            self.log(
                "DEBATE",
                f"🏛️ [Agent Debate on '{item.name}']: Floor ${raw_benchmark.fair_market_unit_price:,.2f} -> "
                f"Council Consensus Established at ${consensus_price:,.2f}",
                debate_transcript
            )

            # Step C: Anomaly Computation based on Consensus
            finding = self.anomaly_engine.evaluate_item(
                item=item,
                benchmark=raw_benchmark,
                consensus_price=consensus_price,
                debate_transcript=debate_transcript
            )
            findings.append(finding)

            if finding.risk_level == "CRITICAL_RED_FLAG":
                self.log(
                    "ALERT",
                    f"⚠️ CRITICAL GOUGING CONFIRMED on '{item.name}': "
                    f"Quoted ${item.quoted_unit_price:,.2f} vs Consensus ${consensus_price:,.2f} "
                    f"(+{finding.gouging_percentage:.1f}%)",
                    finding
                )

        time.sleep(0.1)

        # STAGE 4: SYNTHESIS & DOSSIER GENERATION
        self.log("STAGE_4", "Synthesizing multi-agent council evidence and compiling final Audit Dossier...")
        dossier = self.dossier_generator.compile_dossier(
            tender_id=tender_id,
            title=title,
            procuring_entity=procuring_entity,
            findings=findings
        )

        self.log(
            "COMPLETED",
            f"Audit Complete! Overall Risk Score: {dossier.risk_score}/100. "
            f"Total Taxpayer Funds at Risk: ${dossier.potential_taxpayer_loss:,.2f}",
            dossier
        )

        return dossier
