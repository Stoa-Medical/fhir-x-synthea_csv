"""
ImagingStudy mapper: Synthea imaging_studies.csv row to FHIR R4 ImagingStudy resource.
"""

from typing import Any, Dict, Optional

from ..common.transformers import (
    create_reference,
    to_fhir_datetime,
)


def _generate_id(src: Dict[str, Any]) -> Optional[str]:
    """Generate a deterministic id for convenience and roundtrip correlation."""
    patient = src.get("Patient") or src.get("PATIENT")
    date = src.get("Date") or src.get("DATE")
    series_uid = src.get("Series UID") or src.get("SERIES_UID") or src.get("SERIES UID")
    instance_uid = src.get("Instance UID") or src.get("INSTANCE_UID") or src.get("INSTANCE UID")
    if patient and date and series_uid and instance_uid:
        date_clean = str(date).replace(" ", "").replace(":", "").replace("-", "").replace("T", "")
        return f"imaging-{patient}-{date_clean}-{series_uid}-{instance_uid}"
    return None


def _build_identifier(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    value = src.get("Id") or src.get("ID") or src.get("id")
    if not value:
        return None
    return {"system": "urn:synthea:imaging_studies", "value": str(value)}


def _build_body_site(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    code = (
        src.get("Body Site Code")
        or src.get("BODYSITE_CODE")
        or src.get("BODY_SITE_CODE")
    )
    display = (
        src.get("Body Site Description")
        or src.get("BODYSITE_DESCRIPTION")
        or src.get("BODY_SITE_DESCRIPTION")
    )
    if not code and not display:
        return None
    body_site: Dict[str, Any] = {}
    coding = None
    if code:
        coding = {
            "system": "http://snomed.info/sct",
            "code": str(code),
            "display": display,
        }
    if coding:
        body_site["coding"] = [coding]
    if display:
        body_site["text"] = display
    return body_site if body_site else None


def _build_modality(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    code = src.get("Modality Code") or src.get("MODALITY_CODE")
    display = src.get("Modality Description") or src.get("MODALITY_DESCRIPTION")
    if not code and not display:
        return None
    result: Dict[str, Any] = {"system": "http://dicom.nema.org/resources/ontology/DCM"}
    if code:
        result["code"] = str(code)
    if display:
        result["display"] = str(display)
    return result


def _normalize_sop_code(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    text = str(raw)
    if text.startswith("urn:oid:"):
        return text
    # If looks like plain OID, prefix
    return f"urn:oid:{text}"


def _build_instance(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    instance_uid = src.get("Instance UID") or src.get("INSTANCE_UID") or src.get("INSTANCE UID")
    sop_code = src.get("SOP Code") or src.get("SOP_CODE") or src.get("SOP CODE")
    sop_display = src.get("SOP Description") or src.get("SOP_DESCRIPTION") or src.get("SOP DESCRIPTION")

    instance: Dict[str, Any] = {}
    if instance_uid:
        instance["uid"] = str(instance_uid)

    sop_class = {}
    normalized = _normalize_sop_code(sop_code)
    if normalized:
        sop_class["system"] = "urn:ietf:rfc:3986"
        sop_class["code"] = normalized
    if sop_display:
        sop_class["display"] = str(sop_display)
    if sop_class:
        instance["sopClass"] = sop_class

    return instance if instance else None


def _build_series(src: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    series_uid = src.get("Series UID") or src.get("SERIES_UID") or src.get("SERIES UID")
    series: Dict[str, Any] = {}
    if series_uid:
        series["uid"] = str(series_uid)

    body_site = _build_body_site(src)
    if body_site:
        series["bodySite"] = body_site

    modality = _build_modality(src)
    if modality:
        series["modality"] = modality

    instance = _build_instance(src)
    if instance:
        series["instance"] = [instance]

    return series if series else None


def filter_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v not in (None, "", [], {})}


def imaging_study_transform(src: Dict[str, Any]) -> Dict[str, Any]:
    series = _build_series(src)
    identifiers = []
    identifier = _build_identifier(src)
    if identifier:
        identifiers.append(identifier)

    result: Dict[str, Any] = {
        "resourceType": "ImagingStudy",
        "id": _generate_id(src),
        "status": "available",
        "identifier": identifiers or None,
        "subject": create_reference("Patient", src.get("Patient") or src.get("PATIENT"))
        if (src.get("Patient") or src.get("PATIENT"))
        else None,
        "encounter": create_reference("Encounter", src.get("Encounter") or src.get("ENCOUNTER"))
        if (src.get("Encounter") or src.get("ENCOUNTER"))
        else None,
        "started": to_fhir_datetime(src.get("Date") or src.get("DATE")),
        "series": [series] if series else None,
    }
    return filter_none_values(result)


def map_imaging_study(synthea_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Synthea imaging_studies.csv row to FHIR ImagingStudy.

    Args:
        synthea_row: Dict with CSV fields (case-flexible keys supported)

    Returns:
        FHIR ImagingStudy resource as dict
    """
    return imaging_study_transform(synthea_row)
