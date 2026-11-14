import math
import re
from typing import Any, Optional

def safe_float(val: Any, default: float = 0.0) -> float:
    """
    Bulletproof float converter that NEVER raises ValueError or TypeError.
    Handles:
    - None, empty string '', whitespace
    - Currency symbols: $, €, £, ৳, ₹, ¥, BDT, USD, etc.
    - Formatted numbers: 1,250.50, 12,000,000.00
    - Text with numbers: 'USD 2500/unit', 'approx $85.00'
    - NaN and Inf
    """
    if val is None:
        return default
        
    if isinstance(val, (int, float)):
        if math.isnan(val) or math.isinf(val):
            return default
        return float(val)
        
    s = str(val).strip()
    if not s or s.lower() in ["", "none", "nan", "null", "n/a", "na", "-", "--", "nil", "undefined"]:
        return default

    # Remove currency words
    cleaned = re.sub(r'(?i)\b(usd|bdt|eur|gbp|inr|tk|taka|per unit|each|\/unit)\b', '', s)
    # Remove currency symbols: $, €, £, ৳, ₹, ¥
    cleaned = re.sub(r'[\$\€\£\৳\₹\¥]', '', cleaned)
    # Remove commas
    cleaned = cleaned.replace(',', '').strip()

    # Search for standard float / int
    match = re.search(r'[-+]?\d+(?:\.\d+)?', cleaned)
    if match:
        try:
            res = float(match.group(0))
            if math.isnan(res) or math.isinf(res):
                return default
            return res
        except (ValueError, TypeError):
            pass
            
    return default


def safe_int(val: Any, default: int = 1) -> int:
    """
    Bulletproof integer converter that NEVER raises ValueError or TypeError.
    Handles:
    - Floats/decimals: '10.0' -> 10, 15.8 -> 16
    - Strings with units: '25 units', '5 pcs'
    - None, empty strings -> default
    """
    if val is None:
        return default
        
    if isinstance(val, int):
        return max(1, val)
        
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return default
        return max(1, int(round(val)))
        
    s = str(val).strip()
    if not s or s.lower() in ["", "none", "nan", "null", "n/a", "na", "-", "--", "nil"]:
        return default
        
    # First parse as safe float to cleanly handle '10.0'
    f_val = safe_float(s, default=-1.0)
    if f_val >= 0:
        return max(1, int(round(f_val)))
        
    # Regex fallback
    match = re.search(r'\d+', s)
    if match:
        try:
            return max(1, int(match.group(0)))
        except (ValueError, TypeError):
            pass
            
    return default
