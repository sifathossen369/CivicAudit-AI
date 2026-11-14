import os
import re
import zlib
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
import io
import logging

logger = logging.getLogger("CivicAudit.FileExtractor")

class FileExtractor:
    """
    Universal Zero-Dependency Procurement Document Extractor.
    Extracts text and tabular content from:
    - PDF (.pdf)
    - Excel (.xlsx, .xls)
    - CSV (.csv)
    - Text / JSON (.txt, .json)
    """

    @classmethod
    def extract_text_from_pdf(cls, file_bytes: bytes) -> str:
        """
        Extracts text from PDF bytes.
        Tries pypdf/pdfplumber first; falls back to native stream decompression & text mining.
        """
        # Try third-party library if available
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            text_pages = [page.extract_text() or "" for page in reader.pages]
            full_text = "\n".join(text_pages).strip()
            if len(full_text) > 30:
                return full_text
        except Exception:
            pass

        # Native Zero-Dependency Stream Decompression
        extracted_text = []
        try:
            stream_regex = re.compile(b"stream[\r\n]+(.*?)[\r\n]+endstream", re.DOTALL)
            for match in stream_regex.finditer(file_bytes):
                stream_data = match.group(1)
                decompressed = None
                
                # Try zlib inflate
                try:
                    decompressed = zlib.decompress(stream_data)
                except Exception:
                    # Raw or uncompressed stream
                    decompressed = stream_data

                if decompressed:
                    # Look for Tj text operators: (Sample Text) Tj
                    tj_matches = re.findall(rb"\((.*?)\)\s*Tj", decompressed)
                    for t in tj_matches:
                        try:
                            decoded = t.decode("latin1", errors="ignore").strip()
                            if len(decoded) > 1 and not decoded.startswith("/"):
                                extracted_text.append(decoded)
                        except Exception:
                            pass
                    
                    # Look for TJ array operators: [(Sample) -10 (Text)] TJ
                    array_matches = re.findall(rb"\[(.*?)\]\s*TJ", decompressed)
                    for arr in array_matches:
                        sub_t = re.findall(rb"\((.*?)\)", arr)
                        line_parts = [s.decode("latin1", errors="ignore").strip() for s in sub_t if s.strip()]
                        if line_parts:
                            extracted_text.append(" ".join(line_parts))
        except Exception as e:
            logger.warning(f"Native stream parsing: {e}")

        result = "\n".join(extracted_text).strip()
        
        # If stream extraction was sparse, try raw text string mining
        if len(result) < 40:
            raw_latin = file_bytes.decode("latin1", errors="ignore")
            # Filter clean readable text strings
            clean_strings = re.findall(r'[A-Za-z0-9\$\€\৳\,\.\-\/\:\s]{4,}', raw_latin)
            meaningful = [s.strip() for s in clean_strings if len(s.strip()) > 3 and not s.strip().startswith("/")]
            if meaningful:
                result = "\n".join(meaningful[:250])

        return result

    @classmethod
    def extract_from_excel(cls, file_bytes: bytes) -> str:
        """
        Extracts rows and text from an Excel .xlsx workbook.
        Uses pure-Python zipfile + XML extraction (zero-dependency).
        """
        # Try pandas with openpyxl first if installed
        try:
            import pandas as pd
            df = pd.read_excel(io.BytesIO(file_bytes))
            csv_str = df.to_csv(index=False)
            if len(csv_str) > 20:
                return csv_str
        except Exception:
            pass

        # Native zipfile + XML extraction for .xlsx
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                # Read shared strings
                shared_strings = []
                if "xl/sharedStrings.xml" in z.namelist():
                    tree = ET.fromstring(z.read("xl/sharedStrings.xml"))
                    for elem in tree.iter():
                        if elem.tag.endswith('}t') or elem.tag == 't':
                            shared_strings.append(elem.text or "")

                # Read worksheet (sheet1.xml or any sheet)
                sheet_names = [s for s in z.namelist() if "worksheets/sheet" in s]
                rows_text = []
                if sheet_names:
                    sheet_xml = z.read(sheet_names[0])
                    tree = ET.fromstring(sheet_xml)
                    
                    for row in tree.iter():
                        if row.tag.endswith('}row') or row.tag == 'row':
                            row_cells = []
                            for c in row.iter():
                                if c.tag.endswith('}c') or c.tag == 'c':
                                    cell_type = c.get("t")
                                    val = ""
                                    for child in c:
                                        if child.tag.endswith('}v') or child.tag == 'v':
                                            val = child.text or ""
                                            break
                                    
                                    if cell_type == "s" and val.isdigit():
                                        idx = int(val)
                                        if idx < len(shared_strings):
                                            val = shared_strings[idx]
                                    
                                    if val and val.strip():
                                        row_cells.append(str(val).strip())
                            
                            if len(row_cells) >= 2:
                                rows_text.append(", ".join(row_cells))

                return "\n".join(rows_text)
        except Exception as e:
            logger.warning(f"Native XLSX extraction error: {e}")
            return ""

    @classmethod
    def process_uploaded_file(cls, filename: str, file_bytes: bytes) -> str:
        """
        Auto-detects file type and extracts normalized text suitable for the ProcurementParserTool.
        """
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        
        if ext == "pdf":
            return cls.extract_text_from_pdf(file_bytes)
        elif ext in ["xlsx", "xls"]:
            return cls.extract_from_excel(file_bytes)
        elif ext == "csv":
            for enc in ["utf-8", "latin1", "cp1252"]:
                try:
                    return file_bytes.decode(enc)
                except UnicodeDecodeError:
                    continue
            return file_bytes.decode("utf-8", errors="ignore")
        elif ext in ["txt", "json"]:
            return file_bytes.decode("utf-8", errors="ignore")
        else:
            return file_bytes.decode("utf-8", errors="ignore")
