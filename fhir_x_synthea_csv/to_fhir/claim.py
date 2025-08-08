"""
Claim mapper: Synthea claims.csv row to FHIR R4 Claim resource.

Notes:
- Some lifecycle/adjudication fields (statuses, outstanding) belong to ClaimResponse.
- R5 fields (e.g., Claim.event) are included when helpful; core remains R4-compatible.
"""

from typing import Any, Dict, List, Optional

from ..common.transformers import (
    create_identifier,
    create_reference,
    to_fhir_date,
    to_fhir_datetime,
)


LOCAL_DEPT_URL = "http://synthea.tools/StructureDefinition/department-id"
LOCAL_PDEPT_URL = "http://synthea.tools/StructureDefinition/patient-department-id"
LOCAL_EVENT_SYSTEM = "http://synthea.tools/CodeSystem/claim-event"


def _non_empty(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _build_identifier(src: Dict[str, Any]) -> List[Dict[str, Any]]:
    identifiers: List[Dict[str, Any]] = []
    if cid := _non_empty(src.get("Id")):
        identifiers.append(
            create_identifier(system="urn:synthea:claim", value=cid, use="official")
        )
    return identifiers


def _build_insurance(src: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    entries: List[Dict[str, Any]] = []
    primary = _non_empty(src.get("Primary Patient Insurance ID"))
    secondary = _non_empty(src.get("Secondary Patient Insurance ID"))
    if primary:
        entries.append(
            {
                "sequence": 1,
                "focal": True,
                "coverage": create_reference("Coverage", primary),
            }
        )
    if secondary:
        entries.append(
            {
                "sequence": 2,
                "focal": False,
                "coverage": create_reference("Coverage", secondary),
            }
        )
    return entries or None


def _build_extensions(src: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    extensions: List[Dict[str, Any]] = []
    if dept := _non_empty(src.get("Department ID")):
        extensions.append({"url": LOCAL_DEPT_URL, "valueString": dept})
    if pdept := _non_empty(src.get("Patient Department ID")):
        extensions.append({"url": LOCAL_PDEPT_URL, "valueString": pdept})
    return extensions or None


def _build_diagnoses(src: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    diagnoses: List[Dict[str, Any]] = []
    for i in range(1, 9):
        key = f"Diagnosis{i}"
        code = _non_empty(src.get(key))
        if not code:
            continue
        diagnoses.append(
            {
                "sequence": i,
                "diagnosisCodeableConcept": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": code,
                        }
                    ]
                },
            }
        )
    return diagnoses or None


def _build_care_team(src: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    sup = _non_empty(src.get("Supervising Provider ID"))
    if not sup:
        return None
    return [
        {
            "sequence": 1,
            "provider": create_reference("Practitioner", sup),
            "role": {"text": "supervising"},
        }
    ]


def _build_billable_period(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    service_date = _non_empty(src.get("Service Date"))
    if not service_date:
        return None
    dt = to_fhir_date(service_date) or to_fhir_datetime(service_date)
    return {"start": dt, "end": dt}


def _build_events(src: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    events: List[Dict[str, Any]] = []
    if cid := _non_empty(src.get("Current Illness Date")):
        events.append(
            {
                "type": {"coding": [{"system": LOCAL_EVENT_SYSTEM, "code": "onset"}]},
                "whenDateTime": to_fhir_datetime(cid) or to_fhir_date(cid),
            }
        )
    billed1 = _non_empty(src.get("LastBilledDate1"))
    billed2 = _non_empty(src.get("LastBilledDate2"))
    billedp = _non_empty(src.get("LastBilledDateP"))
    if billed1:
        events.append(
            {
                "type": {"coding": [{"system": LOCAL_EVENT_SYSTEM, "code": "bill-primary"}]},
                "whenDateTime": to_fhir_datetime(billed1) or to_fhir_date(billed1),
            }
        )
    if billed2:
        events.append(
            {
                "type": {"coding": [{"system": LOCAL_EVENT_SYSTEM, "code": "bill-secondary"}]},
                "whenDateTime": to_fhir_datetime(billed2) or to_fhir_date(billed2),
            }
        )
    if billedp:
        events.append(
            {
                "type": {"coding": [{"system": LOCAL_EVENT_SYSTEM, "code": "bill-patient"}]},
                "whenDateTime": to_fhir_datetime(billedp) or to_fhir_date(billedp),
            }
        )
    return events or None


def _build_type(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    type1 = _non_empty(src.get("HealthcareClaimTypeID1"))
    type2 = _non_empty(src.get("HealthcareClaimTypeID2"))
    code_val: Optional[str] = None
    # Prefer primary; fallback to secondary
    for tv in [type1, type2]:
        if tv == "1":
            code_val = "professional"
            break
        if tv == "2":
            code_val = "institutional"
            break
    if not code_val:
        return None
    return {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                "code": code_val,
            }
        ],
        "text": code_val,
    }


def _collect_notes(src: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    notes: List[str] = []
    for k in ("Status1", "Status2", "StatusP"):
        if v := _non_empty(src.get(k)):
            notes.append(f"{k}: {v}")
    for k in ("Outstanding1", "Outstanding2", "OutstandingP"):
        if v := _non_empty(src.get(k)):
            notes.append(f"{k}: {v}")
    return [{"text": t}] if (t := "; ".join(notes)) else None


def map_claim(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a claims.csv row to a FHIR Claim resource dictionary.
    """
    patient_id = _non_empty(row.get("Patient ID"))
    provider_id = _non_empty(row.get("Provider ID"))
    appt_id = _non_empty(row.get("Appointment ID"))

    # Minimal one-item claim capturing encounter and serviced date
    item: Dict[str, Any] = {}
    if appt_id:
        item["encounter"] = [create_reference("Encounter", appt_id)]
    if sd := _non_empty(row.get("Service Date")):
        # Prefer simple date when available
        item["servicedDate"] = to_fhir_date(sd) or to_fhir_datetime(sd)

    claim: Dict[str, Any] = {
        "resourceType": "Claim",
        "id": _non_empty(row.get("Id")),
        "identifier": _build_identifier(row) or None,
        "type": _build_type(row),
        "patient": create_reference("Patient", patient_id) if patient_id else None,
        "provider": create_reference("Practitioner", provider_id) if provider_id else None,
        "insurance": _build_insurance(row),
        "extension": _build_extensions(row),
        "diagnosis": _build_diagnoses(row),
        "careTeam": _build_care_team(row),
        "billablePeriod": _build_billable_period(row),
        "item": [item] if item else None,
        # R5 field; harmless if consumers ignore
        "event": _build_events(row),
        "note": _collect_notes(row),
    }

    # Drop None/empty
    return {k: v for k, v in claim.items() if v is not None}


