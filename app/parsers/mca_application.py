"""MCA application form parser."""

from __future__ import annotations

import re

from app.models.mca_application import MCAApplication, OwnerInfo
from app.utils.currency import find_amount


def parse_mca_application(text: str) -> MCAApplication:
    """Extract fields from an MCA / business funding application."""
    result = MCAApplication()

    # Business legal name
    name_match = re.search(
        r"(?:(?:Legal|Business)\s+Name|Company\s+Name|DBA)[:\s]+(.+?)(?:\n|$)",
        text, re.IGNORECASE,
    )
    if name_match:
        result.business_legal_name = name_match.group(1).strip()

    # DBA
    dba_match = re.search(r"(?:DBA|Doing\s+Business\s+As)[:\s]+(.+?)(?:\n|$)", text, re.IGNORECASE)
    if dba_match:
        result.dba_name = dba_match.group(1).strip()

    # Business address
    addr_match = re.search(
        r"(?:Business\s+)?Address[:\s]+(.+?)(?:\n|$)",
        text, re.IGNORECASE,
    )
    if addr_match:
        result.business_address = addr_match.group(1).strip()

    # Phone
    phone_match = re.search(r"(?:Phone|Telephone|Tel)[:\s]*([\d\(\)\-\.\s]{10,})", text, re.IGNORECASE)
    if phone_match:
        result.phone = phone_match.group(1).strip()

    # Email
    email_match = re.search(r"(?:Email|E-mail)[:\s]*(\S+@\S+)", text, re.IGNORECASE)
    if email_match:
        result.email = email_match.group(1).strip()

    # EIN
    ein_match = re.search(r"(?:EIN|Tax\s+ID|Federal\s+Tax\s+ID)[:\s]*(\d{2}-?\d{7})", text, re.IGNORECASE)
    if ein_match:
        result.ein = ein_match.group(1)

    # Date of incorporation
    inc_match = re.search(
        r"(?:Date\s+(?:of\s+)?Incorporation|Date\s+Established|Inception\s+Date)[:\s]*(\S+)",
        text, re.IGNORECASE,
    )
    if inc_match:
        result.date_of_incorporation = inc_match.group(1).strip()

    # Business type
    for btype in ["LLC", "Corporation", "Corp", "S-Corp", "C-Corp", "Sole Proprietorship", "Sole Prop", "Partnership", "LLP"]:
        if btype.lower() in text.lower():
            result.business_type = btype
            break

    # Monthly/annual revenue
    result.monthly_revenue = find_amount(text, [
        r"[Mm]onthly\s+[Rr]evenue[:\s]*\$?([\d,]+\.?\d*)",
        r"[Aa]vg\.?\s+[Mm]onthly\s+[Ss]ales[:\s]*\$?([\d,]+\.?\d*)",
    ])
    result.annual_revenue = find_amount(text, [
        r"[Aa]nnual\s+[Rr]evenue[:\s]*\$?([\d,]+\.?\d*)",
        r"[Aa]nnual\s+[Ss]ales[:\s]*\$?([\d,]+\.?\d*)",
    ])

    # Requested funding amount
    result.requested_funding_amount = find_amount(text, [
        r"[Rr]equested\s+(?:[Ff]unding\s+)?[Aa]mount[:\s]*\$?([\d,]+\.?\d*)",
        r"[Aa]mount\s+[Rr]equested[:\s]*\$?([\d,]+\.?\d*)",
    ])

    # Owner information (find multiple owners)
    owner_blocks = re.finditer(
        r"(?:Owner|Principal)\s*(?:#?\d*)?\s*(?:Name)?[:\s]+(.+?)(?:\n|$).*?"
        r"(?:Ownership|%|Percent)[:\s]*(\d+\.?\d*)",
        text, re.IGNORECASE | re.DOTALL,
    )
    for match in owner_blocks:
        name = match.group(1).strip()
        pct = float(match.group(2))
        if name:
            result.owners.append(OwnerInfo(name=name, ownership_percent=pct))

    # Current MCA positions
    position_matches = re.findall(
        r"(?:Current\s+)?(?:Position|Advance|MCA)[:\s]+(.+?)(?:\n|$)",
        text, re.IGNORECASE,
    )
    result.current_mca_positions = [p.strip() for p in position_matches if p.strip()]

    # Landlord and rent
    landlord_match = re.search(r"[Ll]andlord[:\s]+(.+?)(?:\n|$)", text)
    if landlord_match:
        result.landlord_name = landlord_match.group(1).strip()

    result.rent_amount = find_amount(text, [
        r"(?:Monthly\s+)?[Rr]ent[:\s]*\$?([\d,]+\.?\d*)",
    ])

    return result
