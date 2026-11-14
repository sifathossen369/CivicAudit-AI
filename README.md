# 🏛️ CivicAudit AI
### Autonomous Public Procurement Oversight & Price-Gouging Forensic Engine

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Track](https://img.shields.io/badge/Track-GovCopilot%20%7C%20Transparent%20Government-orange.svg)](#)
[![Integrity-Score](https://img.shields.io/badge/Forensic%20Compliance-Active-red.svg)](#)

---

## 📌 Executive Summary

Every year, municipal governments and state agencies lose billions of taxpayer dollars to **procurement price-gouging, collusive supplier markups, and inflated Bill of Quantities (BOQ)**. Human auditing committees simply cannot manually cross-reference thousands of disparate line-items against live commercial wholesale benchmarks.

**CivicAudit AI** is an autonomous forensic agent architecture that continuously ingests public municipal tenders, extracts line-item specifications, benchmarks them in real-time against commercial wholesale indices, and compiles an evidence-backed **Forensic Audit Dossier** to flag corrupt overpricing before public contracts are awarded.

---

## ⚙️ Autonomous 4-Stage Forensic Pipeline

```
  [ Municipal Tender PDF / JSON / Text ]
                    │
                    ▼
  ┌───────────────────────────────────────────────┐
  │  Stage 1: Ingestion & BOQ Decomposition       │
  │  (Item, Spec, Quantity, Quoted Unit Rate)     │
  └─────────────────┬─────────────────────────────┘
                    │
                    ▼
  ┌───────────────────────────────────────────────┐
  │  Stage 2: Market Intelligence Inquiry         │
  │  (Live Wholesale Indices, Rate Schedules)     │
  └─────────────────┬─────────────────────────────┘
                    │
                    ▼
  ┌───────────────────────────────────────────────┐
  │  Stage 3: Statistical Gouging Engine          │
  │  (Variance Loss, Gouging %, Risk Score 0-100) │
  └─────────────────┬─────────────────────────────┘
                    │
                    ▼
  ┌───────────────────────────────────────────────┐
  │  Stage 4: Legal & Statutory Dossier Synthesis │
  │  (Executive Memorandum, Red-Flags, PDF/MD)   │
  └───────────────────────────────────────────────┘
```

---

## 🚀 Quickstart & Demo Guide

### 1. Requirements
Ensure you are in the project folder:
```bash
cd C:\Users\sojun\.gemini\antigravity\scratch\civicaudit-ai
```

### 2. Run the Terminal Forensic CLI (Zero Setup)
```bash
python run_audit.py
```
To audit a specific tender docket:
```bash
python run_audit.py --file data/sample_tenders/civil_works_lighting_2025.json
```

### 3. Run the Interactive Web Platform (FastAPI + Tailwind Dashboard)
```bash
python web_server.py
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser for the full interactive visual investigation dashboard with live agent streaming, bar charts, and one-click dossier export.

---

## 📂 Project Architecture

```
civicaudit-ai/
├── config.py                     # Central configuration & thresholds
├── run_audit.py                  # CLI Terminal Entry Point
├── web_server.py                 # FastAPI Web Platform & Live Dashboard
├── core/
│   ├── models.py                 # Pydantic schemas (LineItem, Finding, Dossier)
│   ├── agents/
│   │   └── auditor_orchestrator.py # Multi-stage Lead Forensic Agent
│   ├── tools/
│   │   ├── procurement_parser.py  # BOQ extractor (Text / JSON / Table)
│   │   ├── market_verifier.py     # Live Wholesale & Benchmark Query tool
│   │   ├── anomaly_engine.py      # Mathematical gouging & loss calculator
│   │   └── dossier_generator.py   # Formal audit report compiler
│   └── prompts/
│       └── system_prompts.py      # Forensic legal auditor persona & rules
├── data/
│   └── sample_tenders/            # Ready-to-demo municipal dockets
│       ├── municipal_it_tender_2025.json
│       └── civil_works_lighting_2025.json
└── reports/                      # Auto-generated Forensic Dossiers (.md)
```

---

## 🏆 Key Differentiators for Hackathon Judges

1. **Measurable Fiscal ROI:** Immediately displays *"Taxpayer Money at Risk"* with exact mathematical proof.
2. **Autonomous Tool Dispatches:** Uses multi-step agentic planning rather than a static single-prompt chat.
3. **Statutory Integrity Check:** Maps anomalies directly to public procurement regulations and anti-corruption guidelines.
4. **Dual Interface:** Runs seamlessly both as a high-speed terminal CLI and a high-polish visual executive dashboard.
