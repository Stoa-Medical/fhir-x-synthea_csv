"""
Common transformation functions for FHIR-Synthea CSV mappings.
"""

from datetime import datetime
from typing import Any, Dict, Optional
import chidian.partials as p


def parse_synthea_datetime(dt_str: str) -> Optional[datetime]:
    """Parse Synthea datetime string to Python datetime."""
    if not dt_str:
        return None
    try:
        # Try various formats that Synthea might use
        # ISO 8601 formats first (from FHIR or modern Synthea)
        if 'T' in dt_str:
            # Remove timezone info for parsing
            dt_clean = dt_str.replace('Z', '').split('+')[0].split('-')[0:3]
            dt_clean = '-'.join(dt_clean[0:3])
            if len(dt_str.split('T')) > 1:
                time_part = dt_str.split('T')[1].replace('Z', '').split('+')[0]
                dt_clean = dt_str.split('T')[0] + 'T' + time_part.split('.')[0]
            return datetime.fromisoformat(dt_clean)
        # Traditional Synthea formats
        elif " " in dt_str:
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        else:
            return datetime.strptime(dt_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def format_fhir_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime for FHIR (ISO 8601)."""
    if not dt:
        return None
    return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")


def format_fhir_date(dt: Optional[datetime]) -> Optional[str]:
    """Format date for FHIR (YYYY-MM-DD)."""
    if not dt:
        return None
    return dt.strftime("%Y-%m-%d")


def create_reference(resource_type: str, resource_id: str) -> Dict[str, str]:
    """Create a FHIR reference object."""
    return {"reference": f"{resource_type}/{resource_id}"}


def create_identifier(
    system: str,
    value: str,
    use: Optional[str] = None,
    type_code: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a FHIR identifier object."""
    identifier = {"system": system, "value": str(value)}
    
    if use:
        identifier["use"] = use
    
    if type_code:
        identifier["type"] = {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                    "code": type_code,
                }
            ]
        }
    
    return identifier


# Partial functions for common transformations
split_name = p.split(" ")
first_word = p.split(" ") | p.first
last_word = p.split(" ") | p.last
uppercase = p.upper
lowercase = p.lower
strip_whitespace = p.strip

# Date/time transformers as functions
def to_fhir_datetime(value: str) -> Optional[str]:
    """Transform Synthea datetime to FHIR datetime."""
    if not value:
        return None
    dt = parse_synthea_datetime(value)
    return format_fhir_datetime(dt)

def to_fhir_date(value: str) -> Optional[str]:
    """Transform Synthea datetime to FHIR date."""
    if not value:
        return None
    dt = parse_synthea_datetime(value)
    return format_fhir_date(dt)