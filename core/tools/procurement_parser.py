import io
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
import pandas as pd
from core.models import ProcurementLineItem
from core.llm_client import LLMClient
from core.tools.type_utils import safe_float, safe_int

class ProcurementParserTool:
    """
    Production-Grade Ingestion Tool for Real-World Procurement Documents.
    Zero-Crash Architecture: All conversions are completely shielded against empty strings,
    currency markers, malformed tables, and incomplete data.
    
    Supports:
    1. Structured JSON dockets
    2. Excel & CSV Bill of Quantities (BOQ) spreadsheets
    3. AI LLM Semantic Extraction (for messy PDFs, scanned layouts, OCR text)
    4. Heuristic tabular and regex parsing fallback
    """
    name: str = "procurement_parser"
    description: str = "Extracts procurement line items from JSON, CSV, Excel, and raw PDF text/tables."

    @staticmethod
    def parse_from_json(json_data: Dict[str, Any]) -> List[ProcurementLineItem]:
        items: List[ProcurementLineItem] = []
        raw_items = json_data.get("items") or json_data.get("line_items") or json_data.get("boq_items") or []
        
        for idx, it in enumerate(raw_items, 1):
            if not isinstance(it, dict):
                continue
            name = str(it.get("name") or it.get("item_name") or it.get("description") or f"Procurement Item {idx}").strip()
            if not name or name.lower() in ["total", "grand total", "subtotal", "sub-total", "vat", "tax"]:
                continue
                
            spec = str(it.get("specification") or it.get("specs") or "Standard commercial specification").strip()
            category = str(it.get("category") or "General Goods").strip()
            quantity = safe_int(it.get("quantity", 1), default=1)
            
            unit_price = safe_float(it.get("quoted_unit_price") or it.get("unit_price") or it.get("rate") or 0.0)
            total_price = safe_float(it.get("quoted_total_price") or it.get("total_price") or it.get("amount") or 0.0)
            
            # Cross-calculate if one is missing
            if unit_price <= 0 and total_price > 0:
                unit_price = round(total_price / max(1, quantity), 2)
            elif total_price <= 0 and unit_price > 0:
                total_price = round(unit_price * max(1, quantity), 2)
                
            items.append(ProcurementLineItem(
                item_id=str(it.get("item_id") or f"BOQ-{idx:03d}"),
                name=name,
                specification=spec,
                category=category,
                quantity=quantity,
                quoted_unit_price=unit_price,
                quoted_total_price=total_price
            ))
        return items

    @staticmethod
    def parse_from_csv(csv_path_or_buffer: Union[str, Path, io.StringIO, Any]) -> List[ProcurementLineItem]:
        try:
            if isinstance(csv_path_or_buffer, str):
                if "\n" in csv_path_or_buffer or "\r" in csv_path_or_buffer:
                    cleaned_csv = re.sub(r'(?<=\d),(?=\d{3}\b)', '', csv_path_or_buffer)
                    df = pd.read_csv(io.StringIO(cleaned_csv), index_col=False)
                else:
                    with open(csv_path_or_buffer, 'r', encoding='utf-8', errors='ignore') as f:
                        cleaned_csv = re.sub(r'(?<=\d),(?=\d{3}\b)', '', f.read())
                    df = pd.read_csv(io.StringIO(cleaned_csv), index_col=False)
            elif hasattr(csv_path_or_buffer, "read"):
                raw_c = csv_path_or_buffer.read()
                if isinstance(raw_c, bytes):
                    raw_c = raw_c.decode('utf-8', errors='ignore')
                cleaned_csv = re.sub(r'(?<=\d),(?=\d{3}\b)', '', raw_c)
                df = pd.read_csv(io.StringIO(cleaned_csv), index_col=False)
            else:
                df = pd.read_csv(csv_path_or_buffer, index_col=False)
        except Exception:
            return []

        id_col = None
        name_col = None
        spec_col = None
        category_col = None
        qty_col = None
        price_col = None
        total_col = None

        # Two-pass column detection: Pass 1 identifies specific columns, Pass 2 matches remaining
        for col in df.columns:
            c_str = str(col).lower().strip()
            c_clean = re.sub(r'[\(\)\[\]\$\€\৳\£\/]', ' ', c_str).strip()
            tokens = c_clean.split()
            
            # 1. Price column detection (Must NOT be total)
            if any(k in c_clean for k in ["unit rate", "unit price", "unit cost", "rate unit", "price unit"]) or (
                any(k in tokens for k in ["rate", "price", "cost"]) and not any(t in tokens for t in ["total", "sum", "subtotal", "amount"])
            ):
                if not price_col:
                    price_col = col
            # 2. Total column detection
            elif any(k in c_clean for k in ["total price", "total amount", "quoted total", "line total", "subtotal", "sub total"]) or any(t in tokens for t in ["total", "amount"]):
                if not total_col:
                    total_col = col
            # 3. Quantity column detection
            elif any(k in tokens for k in ["qty", "quantity", "count", "units", "unit", "nos", "number", "volume"]):
                if not qty_col:
                    qty_col = col
            # 4. Item ID / Code column detection (Strict: must have id, code, or sl)
            elif any(k in c_clean for k in ["item id", "item code", "item_id", "item_code", "product code", "sl no", "sl.", "serial no"]) or (
                any(t in tokens for t in ["id", "code", "sl"]) and not any(t in tokens for t in ["description", "particulars", "name"])
            ):
                if not id_col:
                    id_col = col
            # 5. Specification column detection
            elif any(k in c_clean for k in ["specification", "specifications", "technical specs", "technical specification", "specs", "brand", "model"]):
                if not spec_col:
                    spec_col = col
            # 6. Category column detection
            elif any(k in c_clean for k in ["category", "categories", "department", "sector", "class"]):
                if not category_col:
                    category_col = col
            # 7. Item Name / Description column detection (Explicitly avoid pure ID/Code columns)
            elif any(k in c_clean for k in [
                "item description", "particulars", "description", "goods", "equipment",
                "asset", "material", "product name", "item name", "name of item"
            ]) or (
                any(t in tokens for t in ["name", "item", "title"]) and not any(t in tokens for t in ["id", "code", "sl", "no"])
            ):
                if not name_col:
                    name_col = col

        # Fallback if name_col was not detected: pick first column that is not price/total/qty
        if not name_col:
            for col in df.columns:
                if col not in [price_col, total_col, qty_col, id_col]:
                    name_col = col
                    break

        items: List[ProcurementLineItem] = []
        if name_col and (price_col or total_col):
            for idx, row in df.iterrows():
                try:
                    raw_name = str(row[name_col]).strip()
                    if not raw_name or raw_name.lower() in [
                        "nan", "none", "null", "total", "grand total", "subtotal", "sub-total",
                        "vat", "tax", "signature", "authorized signature", "date"
                    ]:
                        continue

                    # Extract ID and clean product name
                    raw_id = str(row[id_col]).strip() if id_col and pd.notna(row[id_col]) else ""
                    if not raw_id or raw_id.lower() in ["nan", "none"]:
                        raw_id = f"CSV-{idx+1:03d}"

                    clean_name = raw_name
                    # Only search for prefix code if ID was not already provided by an ID column
                    if raw_id.startswith("CSV-") or not raw_id:
                        code_match = re.match(r'^([A-Z0-9\-_]{2,10})\s*[:\|\.]\s*(.+)$|^([A-Z0-9\-_]{2,10})\s+-\s+(.+)$', raw_name)
                        if code_match:
                            extracted_code = (code_match.group(1) or code_match.group(3)).strip()
                            clean_name = (code_match.group(2) or code_match.group(4)).strip()
                            raw_id = extracted_code

                    # If clean_name is purely a short code (e.g. "CIV-049") and spec_col has real text
                    if re.match(r'^[A-Z0-9\-_]{2,10}$', clean_name) and spec_col and pd.notna(row[spec_col]):
                        spec_text = str(row[spec_col]).strip()
                        if spec_text and len(spec_text) > 3:
                            if raw_id.startswith("CSV-") or not raw_id:
                                raw_id = clean_name
                            clean_name = spec_text

                    # Extract Specification and Category
                    spec = str(row[spec_col]).strip() if spec_col and pd.notna(row[spec_col]) else "Standard commercial specification"
                    category = str(row[category_col]).strip() if category_col and pd.notna(row[category_col]) else "Procurement Asset"
                        
                    qty = safe_int(row[qty_col], default=1) if qty_col and pd.notna(row[qty_col]) else 1
                    
                    unit_price = safe_float(row[price_col], default=0.0) if price_col and pd.notna(row[price_col]) else 0.0
                    total_price = safe_float(row[total_col], default=0.0) if total_col and pd.notna(row[total_col]) else 0.0
                    
                    if unit_price <= 0 and total_price > 0:
                        unit_price = round(total_price / max(1, qty), 2)
                    elif total_price <= 0 and unit_price > 0:
                        total_price = round(unit_price * max(1, qty), 2)
                        
                    if unit_price > 0 or total_price > 0:
                        items.append(ProcurementLineItem(
                            item_id=raw_id,
                            name=clean_name,
                            specification=spec,
                            category=category,
                            quantity=qty,
                            quoted_unit_price=unit_price,
                            quoted_total_price=total_price
                        ))
                except Exception:
                    continue
        return items

    @staticmethod
    def parse_from_text(raw_text: str) -> List[ProcurementLineItem]:
        """
        Multi-Stage Ingestion Pipeline:
        1. AI LLM Extraction (high-accuracy semantic parsing for messy PDF / OCR text)
        2. Direct CSV / Tabular parsing if data resembles structured rows
        3. Heuristic regex and delimiter parsing fallback (zero-dependency)
        """
        if not raw_text or not raw_text.strip():
            return []

        # Stage A: Try AI LLM Extraction if API is online
        if LLMClient.is_available():
            try:
                llm_items = LLMClient.parse_messy_tender_text(raw_text)
                if llm_items and isinstance(llm_items, list):
                    extracted = []
                    for idx, it in enumerate(llm_items, 1):
                        if not isinstance(it, dict):
                            continue
                        raw_name = str(it.get("name") or it.get("item_name") or f"Procurement Item {idx}").strip()
                        if not raw_name or raw_name.lower() in ["total", "subtotal", "grand total", "vat", "tax"]:
                            continue
                        raw_id = str(it.get("item_id") or it.get("code") or f"AI-{idx:03d}").strip()
                        
                        # Separate prefix code if present
                        code_m = re.match(r'^([A-Z0-9\-_]{2,10})\s*[:\|\-\.\)]\s*(.+)$', raw_name)
                        if code_m:
                            raw_id = code_m.group(1).strip()
                            raw_name = code_m.group(2).strip()
                            
                        qty = safe_int(it.get("quantity", 1), default=1)
                        unit_price = safe_float(it.get("quoted_unit_price", 0.0), default=0.0)
                        
                        if unit_price > 0:
                            extracted.append(ProcurementLineItem(
                                item_id=raw_id,
                                name=raw_name,
                                specification=str(it.get("specification") or "AI Extracted Specification"),
                                category=str(it.get("category") or "AI Ingested"),
                                quantity=qty,
                                quoted_unit_price=unit_price,
                                quoted_total_price=round(unit_price * qty, 2)
                            ))
                    if extracted:
                        return extracted
            except Exception:
                pass

        # Stage B: Try Structured CSV Parsing only if text has genuine CSV structure (commas and no pipes)
        if "," in raw_text and ("\n" in raw_text or "\r" in raw_text) and "|" not in raw_text:
            try:
                csv_items = ProcurementParserTool.parse_from_csv(raw_text)
                if csv_items and len(csv_items) >= 1:
                    return csv_items
            except Exception:
                pass

        # Stage C: Deterministic Heuristic Line Parsing
        items: List[ProcurementLineItem] = []
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        item_counter = 1

        for line in lines:
            # Skip obvious header/footer rows
            if line.lower().startswith(("page ", "total", "subtotal", "grand total", "signature", "date:")):
                continue

            # Case 1: Tabular split by tabs, pipes, or 2+ spaces
            parts = [p.strip() for p in re.split(r'[\t|]+|\s{2,}', line) if p.strip()]
            if len(parts) >= 3:
                # Detect if parts[0] is an ID/Code (e.g. "IT-008", "CIV-049", "1.")
                first_part = parts[0]
                is_id = bool(re.match(r'^[A-Z0-9\-_]{2,10}$', first_part) or re.match(r'^\d{1,4}[\.\)]?$', first_part))
                
                if is_id and len(parts) >= 3:
                    item_id = first_part.rstrip('.)')
                    cand_name = parts[1]
                    remaining = parts[2:]
                else:
                    item_id = f"BOQ-{item_counter:03d}"
                    cand_name = first_part
                    remaining = parts[1:]

                # Check if cand_name has a prefix code e.g. "CIV-049 - Excavator"
                if item_id.startswith("BOQ-") or not item_id:
                    code_m = re.match(r'^([A-Z0-9\-_]{2,10})\s*[:\|\.]\s*(.+)$|^([A-Z0-9\-_]{2,10})\s+-\s+(.+)$', cand_name)
                    if code_m:
                        extracted_code = (code_m.group(1) or code_m.group(3)).strip()
                        cand_name = (code_m.group(2) or code_m.group(4)).strip()
                        item_id = extracted_code

                # Separate numeric vs text columns from remaining
                valid_nums = []
                spec_tokens = []
                for p in remaining:
                    val = safe_float(p, default=-1.0)
                    if val >= 0 and re.search(r'\d', p):
                        valid_nums.append(val)
                    else:
                        spec_tokens.append(p)

                if len(valid_nums) >= 1:
                    if len(valid_nums) == 1:
                        qty = 1
                        unit_price = valid_nums[0]
                    else:
                        qty = safe_int(valid_nums[0], default=1)
                        unit_price = valid_nums[1]

                    spec = " ".join(spec_tokens) if spec_tokens else "Standard tender technical specifications"

                    if unit_price > 0 and len(cand_name) > 1:
                        items.append(ProcurementLineItem(
                            item_id=item_id,
                            name=cand_name,
                            specification=spec,
                            category="Procurement Asset",
                            quantity=qty,
                            quoted_unit_price=unit_price,
                            quoted_total_price=round(unit_price * qty, 2)
                        ))
                        item_counter += 1
                        continue

            # Case 2: Comma or @ or colon separated pattern
            # Matches: "CIV-049: 20-Ton Hydraulic Excavator, 3 units @ $58,000" or "Executive Laptop, 10 units @ $2500"
            match = re.search(
                r"^(?:([A-Z0-9\-_]{2,10})\s*[:\|\-\.\)]\s*)?([^,@|]+?)(?:,\s*|\s*\|\s*|\s*:\s*|\s*-\s*)(\d+)\s*(?:units?|pcs|qty|nos)?\s*(?:@|at)?\s*[\$€৳£]?\s*([0-9,]+(?:\.[0-9]{2})?)",
                line,
                re.IGNORECASE
            )
            if match:
                extracted_id = match.group(1).strip() if match.group(1) else f"BOQ-{item_counter:03d}"
                name = match.group(2).strip()
                qty = safe_int(match.group(3), default=1)
                unit_price = safe_float(match.group(4), default=0.0)
                
                if unit_price > 0 and len(name) > 2:
                    items.append(ProcurementLineItem(
                        item_id=extracted_id,
                        name=name,
                        specification="Standard procurement grade",
                        category="Municipal Asset",
                        quantity=qty,
                        quoted_unit_price=unit_price,
                        quoted_total_price=round(unit_price * qty, 2)
                    ))
                    item_counter += 1
                    continue

        return items
