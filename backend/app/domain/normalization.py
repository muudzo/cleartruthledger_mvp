
from typing import Dict, Any
from decimal import Decimal

def canonicalize_event_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produces a deterministic, canonical version of event data.
    
    Rules:
    1. Sorts all keys (recursive).
    2. Normalizes Currency codes to UPPERCASE.
    3. Normalizes Amounts to string with fixed 2-decimal precision (for MVP).
    4. Ensures 'direction' is explicit if present (though often part of LedgerEntry, not raw event).
    5. Strips whitespace from strings? (Optional, let's stick to key rules first).
    """
    canonical = {}
    
    # Sort keys
    sorted_keys = sorted(data.keys())
    
    for key in sorted_keys:
        value = data[key]
        
        # KEY SPECIFIC NORMALIZATION
        if key == "currency":
            if isinstance(value, str):
                value = value.upper()
        
        elif key == "amount":
            # Normalize to 2 decimal places string
            # Handle float, int, str, Decimal
            try:
                d = Decimal(str(value))
                # Quantize to 2 decimals
                value = f"{d:.2f}"
            except:
                value = str(value) # Fallback if not debatable
        
        elif hasattr(value, "isoformat"):
            # Handle datetime, date
            value = value.isoformat()
                
        # RECURSIVE SORTING
        elif isinstance(value, dict):
            value = canonicalize_event_data(value)
            
        elif isinstance(value, list):
            # For lists, we can't easily sort unless we know they are sets.
            # Preserving order is usually safer for lists unless specified otherwise.
            # But we should canonicalize items inside.
            new_list = []
            for item in value:
                if isinstance(item, dict):
                    new_list.append(canonicalize_event_data(item))
                else:
                    new_list.append(item)
            value = new_list
            
        canonical[key] = value
        
    return canonical
