"""
Claim reverse mapper: FHIR R4 Claim resource to Synthea claims.csv row.

Fields that are not present in Claim (e.g., adjudication status, outstanding balances)
are left blank; they are expected to come from ClaimResponse elsewhere.
"""

from typing import Any, Dict, List, Optional, Tuple

from ..common.reverse_transformers import (
    extract_reference_id,
    extract_coding_by_system,
    parse_fhir_date,
    parse_fhir_datetime,
)


LOCAL_DEPT_URL = "http://synthea.tools/StructureDefinition/department-id"
LOCAL_PDEPT_URL = "http://synthea.tools/StructureDefinition/patient-department-id"
LOCAL_EVENT_SYSTEM = "http://synthea.tools/CodeSystem/claim-event"


def _safe(value: Optional[Any]) -> str:
    return "" if value is None else str(value)


def _primary_secondary_coverage_ids(insurance: Optional[List[Dict[str, Any]]]) -> Tuple[Optional[str], Optional[str]]:
    if not insurance or not isinstance(insurance, list):
        return None, None
    primary: Optional[str] = None
    secondary: Optional[str] = None
    # Prefer focal=true as primary, then sequence order
    sorted_ins = sorted(insurance, key=lambda e: (not e.get("focal", False), e.get("sequence") or 99))
    for idx, ins in enumerate(sorted_ins):
        cov_id = extract_reference_id(ins.get("coverage"))
        if not cov_id:
            continue
        if primary is None:
            primary = cov_id
        elif secondary is None:
            secondary = cov_id
    return primary, secondary


def _extract_type_ids(claim: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    ctype = claim.get("type")
    code = None
    if isinstance(ctype, dict):
        coding = ctype.get("coding")
        if isinstance(coding, list) and coding:
            first = coding[0]
            if isinstance(first, dict):
                code = first.get("code") or ctype.get("text")
    # Map to 1/2
    if code == "professional":
        return "1", None
    if code == "institutional":
        return "2", None
    return None, None


def _extract_diagnosis_codes(claim: Dict[str, Any]) -> List[str]:
    out: List[str] = ["" for _ in range(8)]
    diags = claim.get("diagnosis") or []
    for d in diags:
        if not isinstance(d, dict):
            continue
        seq = d.get("sequence")
        concept = d.get("diagnosisCodeableConcept")
        coding = None
        if isinstance(concept, dict):
            coding = extract_coding_by_system(concept, "http://snomed.info/sct") or (
                (concept.get("coding") or [{}])[0] if concept.get("coding") else None
            )
        code = None
        if isinstance(coding, dict):
            code = coding.get("code") or concept.get("text") if isinstance(concept, dict) else None
        if isinstance(seq, int) and 1 <= seq <= 8 and code:
            out[seq - 1] = str(code)
    return out


def _extract_event_date(claim: Dict[str, Any], code: str) -> Optional[str]:
    events = claim.get("event")
    if not isinstance(events, list):
        return None
    for e in events:
        if not isinstance(e, dict):
            continue
        etype = e.get("type")
        coding = (etype or {}).get("coding") if isinstance(etype, dict) else None
        if isinstance(coding, list):
            for c in coding:
                if isinstance(c, dict) and c.get("system") == LOCAL_EVENT_SYSTEM and c.get("code") == code:
                    return parse_fhir_datetime(e.get("whenDateTime"))
    return None


def map_fhir_claim_to_claims_row(claim: Dict[str, Any]) -> Dict[str, Any]:
    if not claim or claim.get("resourceType") != "Claim":
        raise ValueError("Input must be a FHIR Claim resource")

    rid = claim.get("id")
    patient_id = extract_reference_id(claim.get("patient"))
    provider_id = extract_reference_id(claim.get("provider"))
    primary_cov, secondary_cov = _primary_secondary_coverage_ids(claim.get("insurance"))

    # Department extensions
    dept = ""
    pdept = ""
    exts = claim.get("extension")
    if isinstance(exts, list):
        for ext in exts:
            if not isinstance(ext, dict):
                continue
            if ext.get("url") == LOCAL_DEPT_URL and ext.get("valueString") is not None:
                dept = str(ext.get("valueString"))
            if ext.get("url") == LOCAL_PDEPT_URL and ext.get("valueString") is not None:
                pdept = str(ext.get("valueString"))

    # Diagnosis codes
    diag_codes = _extract_diagnosis_codes(claim)

    # Appointment from first item.encounter
    appt_id = ""
    items = claim.get("item") or []
    if isinstance(items, list) and items:
        first = items[0]
        if isinstance(first, dict):
            encs = first.get("encounter") or []
            if isinstance(encs, list) and encs:
                appt_id = _safe(extract_reference_id(encs[0]))

    # Service date from billablePeriod.start (fallback to end)
    bill = claim.get("billablePeriod") or {}
    service_date = parse_fhir_date(bill.get("start")) or parse_fhir_date(bill.get("end"))

    # Current illness and billed dates from events
    current_illness = _extract_event_date(claim, "onset") or ""
    last_billed1 = _extract_event_date(claim, "bill-primary") or ""
    last_billed2 = _extract_event_date(claim, "bill-secondary") or ""
    last_billedp = _extract_event_date(claim, "bill-patient") or ""

    # Supervising provider
    supervising = ""
    care_team = claim.get("careTeam")
    if isinstance(care_team, list):
        for entry in care_team:
            if not isinstance(entry, dict):
                continue
            role = entry.get("role")
            role_text = (role or {}).get("text") if isinstance(role, dict) else None
            if (role_text and role_text.lower() == "supervising") or not role_text:
                supervising = _safe(extract_reference_id(entry.get("provider")))
                if supervising:
                    break

    # Claim type mapping
    type1, type2 = _extract_type_ids(claim)

    row: Dict[str, Any] = {
        "Id": _safe(rid),
        "Patient ID": _safe(patient_id),
        "Provider ID": _safe(provider_id),
        "Primary Patient Insurance ID": _safe(primary_cov),
        "Secondary Patient Insurance ID": _safe(secondary_cov),
        "Department ID": dept,
        "Patient Department ID": pdept,
        "Referring Provider ID": "",  # not derivable from Claim alone
        "Appointment ID": _safe(appt_id),
        "Current Illness Date": _safe(current_illness),
        "Service Date": _safe(service_date),
        "Supervising Provider ID": _safe(supervising),
        # Status/Outstanding come from ClaimResponse; left blank
        "Status1": "",
        "Status2": "",
        "StatusP": "",
        "Outstanding1": "",
        "Outstanding2": "",
        "OutstandingP": "",
        "LastBilledDate1": _safe(last_billed1),
        "LastBilledDate2": _safe(last_billed2),
        "LastBilledDateP": _safe(last_billedp),
        "HealthcareClaimTypeID1": _safe(type1),
        "HealthcareClaimTypeID2": _safe(type2),
    }

    # Fill Diagnosis1..8
    for i in range(8):
        row[f"Diagnosis{i+1}"] = diag_codes[i] if i < len(diag_codes) else ""

    return row


