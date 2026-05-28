from __future__ import annotations

import csv
import io
import statistics
from datetime import date, datetime, timedelta
from typing import Iterable

from django.db import transaction

from .airports import AIRPORTS, route_distance_km
from .models import (
    AuditEntry,
    EmissionFactor,
    NormalizedRecord,
    RawRecord,
    UploadBatch,
)


UNAMBIGUOUS_DATE_FORMATS = (
    "%Y-%m-%d",
    "%d.%m.%Y",
    "%d-%b-%Y",
    "%d-%b-%y",
)


def parse_date(value: str) -> tuple[date | None, str | None]:
    if value is None:
        return None, "missing date"
    s = value.strip()
    if not s:
        return None, "missing date"

    for fmt in UNAMBIGUOUS_DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date(), None
        except ValueError:
            continue

    if "/" in s:
        mdy = None
        dmy = None
        try:
            mdy = datetime.strptime(s, "%m/%d/%Y").date()
        except ValueError:
            pass
        try:
            dmy = datetime.strptime(s, "%d/%m/%Y").date()
        except ValueError:
            pass

        if mdy and dmy and mdy != dmy:
            return mdy, f"ambiguous slash-date '{s}', assumed MM/DD/YYYY"
        if mdy:
            return mdy, None
        if dmy:
            return dmy, None

    return None, f"unparseable date '{s}'"


def find_factor(category: str, unit: str, year: int) -> EmissionFactor | None:
    return EmissionFactor.objects.filter(
        category=category, unit=unit, valid_year=year
    ).first()


def _merge_flag(existing: str, new: str) -> str:
    if not existing:
        return new
    if not new:
        return existing
    return f"{existing}; {new}"


def _audit_create(record: NormalizedRecord, who: str) -> None:
    AuditEntry.objects.create(
        normalized_record=record,
        action="CREATED",
        changed_by=who,
        note="row ingested from CSV",
    )


def _parse_csv(file_bytes: bytes) -> list[dict]:
    text = file_bytes.decode("utf-8-sig", errors="replace")
    return list(csv.DictReader(io.StringIO(text)))


SAP_FUEL_WARENGRUPPE = "300"

SAP_FUEL_KEYWORDS = (
    ("Diesel", "diesel"),
    ("Petrol", "petrol"),
    ("Lubricant", "lubricant"),
    ("CNG", "cng"),
    ("Natural Gas", "cng"),
)

GAL_TO_L = 3.785


def _sap_pick_factor_category(short_text: str) -> str | None:
    t = (short_text or "").lower()
    for keyword, category in SAP_FUEL_KEYWORDS:
        if keyword.lower() in t:
            return category
    return None


@transaction.atomic
def ingest_sap(batch: UploadBatch, file_bytes: bytes, who: str) -> list[NormalizedRecord]:
    rows = _parse_csv(file_bytes)
    created: list[NormalizedRecord] = []

    for i, row in enumerate(rows, start=1):
        raw = RawRecord.objects.create(
            tenant=batch.tenant, batch=batch, row_number=i, raw_data=row,
        )

        flag_reason = ""
        activity_date, date_flag = parse_date(row.get("Bestelldatum", ""))
        if date_flag:
            flag_reason = _merge_flag(flag_reason, date_flag)
        if activity_date is None:
            activity_date = date.today()


        warengruppe = (row.get("Warengruppe") or "").strip()
        if warengruppe == SAP_FUEL_WARENGRUPPE:
            scope = 1
        else:
            scope = 3

        bme = (row.get("BME") or "").strip()
        try:
            qty = float((row.get("Bestellmenge") or "0").strip() or 0)
        except ValueError:
            qty = 0.0
            flag_reason = _merge_flag(flag_reason, "unparseable quantity")

        activity_value = qty
        activity_unit = bme

        if not bme:
            flag_reason = _merge_flag(flag_reason, "missing unit, cannot compute")
        elif bme == "GAL":
            activity_value = qty * GAL_TO_L
            activity_unit = "L"
            flag_reason = _merge_flag(flag_reason, "gallons converted to litres, confirm")
        elif bme in ("ST", "EA"):
            flag_reason = _merge_flag(
                flag_reason, f"unit '{bme}' is count-based, no emission factor"
            )

        factor: EmissionFactor | None = None
        co2e_kg = None

        if scope == 3:
            flag_reason = _merge_flag(
                flag_reason, "procurement emission factor not in MVP scope"
            )
        elif activity_unit and bme not in ("ST", "EA", ""):
            category = _sap_pick_factor_category(row.get("Short_Text", ""))
            if category is None:
                flag_reason = _merge_flag(
                    flag_reason,
                    f"no emission factor matched Short_Text='{row.get('Short_Text')}'",
                )
            else:
                factor = find_factor(category, activity_unit, activity_date.year)
                if factor is None:
                    flag_reason = _merge_flag(
                        flag_reason,
                        f"no emission factor for {category} in {activity_unit}/{activity_date.year}",
                    )
                else:
                    co2e_kg = activity_value * factor.factor_value

        status = "FLAGGED" if flag_reason else "CLEAN"

        norm = NormalizedRecord.objects.create(
            tenant=batch.tenant,
            raw_record=raw,
            source="SAP",
            scope=scope,
            activity_value=activity_value,
            activity_unit=activity_unit,
            activity_date=activity_date,
            emission_factor=factor,
            co2e_kg=co2e_kg,
            review_status=status,
            flag_reason=flag_reason,
        )
        _audit_create(norm, who)
        created.append(norm)

    batch.row_count = len(rows)
    batch.save(update_fields=["row_count"])
    return created


UTILITY_SPIKE_MULTIPLIER = 2.5


def _split_bill_by_month(start: date, end: date, kwh: float) -> list[tuple[date, float]]:
    if end < start:
        return [(start.replace(day=1), kwh)]

    total_days = (end - start).days + 1
    buckets: dict[date, int] = {}
    cursor = start
    while cursor <= end:
        month_key = cursor.replace(day=1)
        buckets[month_key] = buckets.get(month_key, 0) + 1
        cursor += timedelta(days=1)

    return [
        (month_first, kwh * (days / total_days))
        for month_first, days in buckets.items()
    ]


@transaction.atomic
def ingest_utility(batch: UploadBatch, file_bytes: bytes, who: str) -> list[NormalizedRecord]:
    rows = _parse_csv(file_bytes)
    created: list[NormalizedRecord] = []

    grid_factor = find_factor("grid_electricity_IN", "kWh", 2024)
    pending: list[tuple[RawRecord, str, str, date, float]] = []

    for i, row in enumerate(rows, start=1):
        raw = RawRecord.objects.create(
            tenant=batch.tenant, batch=batch, row_number=i, raw_data=row,
        )

        row_flag = ""
        start, start_flag = parse_date(row.get("Period_Start", ""))
        end, end_flag = parse_date(row.get("Period_End", ""))
        if start_flag:
            row_flag = _merge_flag(row_flag, f"period_start: {start_flag}")
        if end_flag:
            row_flag = _merge_flag(row_flag, f"period_end: {end_flag}")

        try:
            kwh = float((row.get("Units_kWh") or "0").strip() or 0)
        except ValueError:
            kwh = 0.0
            row_flag = _merge_flag(row_flag, "unparseable Units_kWh")

        account = (row.get("Account_No") or "").strip()
        reading_type = (row.get("Reading_Type") or "").strip()

        if start is None or end is None:
            placeholder_month = (start or end or date.today()).replace(day=1)
            pending.append((raw, account, reading_type, placeholder_month, kwh))
            raw._row_flag = _merge_flag(row_flag, "missing period dates, no monthly split")
            continue

        raw._row_flag = row_flag
        for month_first, share in _split_bill_by_month(start, end, kwh):
            pending.append((raw, account, reading_type, month_first, share))

    per_account_kwh: dict[str, list[float]] = {}
    for _, account, _, _, share in pending:
        per_account_kwh.setdefault(account, []).append(share)
    account_median = {
        acct: (statistics.median(vals) if vals else 0.0)
        for acct, vals in per_account_kwh.items()
    }

    for raw, account, reading_type, month_first, share in pending:
        flag_reason = getattr(raw, "_row_flag", "") or ""

        if reading_type.lower() == "estimated":
            flag_reason = _merge_flag(
                flag_reason, "estimated reading, lower confidence"
            )

        median = account_median.get(account, 0.0)
        if median > 0 and share > UTILITY_SPIKE_MULTIPLIER * median:
            flag_reason = _merge_flag(
                flag_reason,
                f"anomalous consumption spike, verify (share={share:.0f}kWh "
                f"vs median={median:.0f}kWh)",
            )

        factor = grid_factor
        co2e_kg = share * factor.factor_value if factor else None
        if factor is None:
            flag_reason = _merge_flag(flag_reason, "no grid factor seeded for 2024")

        status = "FLAGGED" if flag_reason else "CLEAN"
        norm = NormalizedRecord.objects.create(
            tenant=batch.tenant,
            raw_record=raw,
            source="UTILITY",
            scope=2,
            activity_value=share,
            activity_unit="kWh",
            activity_date=month_first,
            emission_factor=factor,
            co2e_kg=co2e_kg,
            review_status=status,
            flag_reason=flag_reason,
        )
        _audit_create(norm, who)
        created.append(norm)

    batch.row_count = len(rows)
    batch.save(update_fields=["row_count"])
    return created


FLIGHT_ROUTING_UPLIFT = 1.09

CABIN_ECONOMY = {"Y", "ECON", "ECONOMY"}
CABIN_BUSINESS = {"C", "J", "BUSINESS"}


def _normalize_cabin(raw_class: str) -> tuple[str | None, str | None]:
    c = (raw_class or "").strip()
    if not c:
        return None, None
    upper = c.upper()
    if upper in CABIN_ECONOMY:
        return "economy", None
    if upper in CABIN_BUSINESS:
        return "business", None
    return "economy", f"unrecognized cabin class '{c}', defaulted to economy"


def _is_multileg(description: str) -> bool:
    first_token = (description or "").strip().split()[:1]
    return bool(first_token) and first_token[0].count("-") >= 2


def _car_days(row: dict) -> int:
    n = (row.get("Nights") or "").strip()
    try:
        return max(1, int(float(n)))
    except (TypeError, ValueError):
        return 1


@transaction.atomic
def ingest_travel(batch: UploadBatch, file_bytes: bytes, who: str) -> list[NormalizedRecord]:
    rows = _parse_csv(file_bytes)
    created: list[NormalizedRecord] = []

    for i, row in enumerate(rows, start=1):
        raw = RawRecord.objects.create(
            tenant=batch.tenant, batch=batch, row_number=i, raw_data=row,
        )

        flag_reason = ""
        activity_date, date_flag = parse_date(row.get("Date", ""))
        if date_flag:
            flag_reason = _merge_flag(flag_reason, date_flag)
        if activity_date is None:
            activity_date = date.today()

        ttype = (row.get("Type") or "").strip().upper()
        origin = (row.get("Origin") or "").strip().upper()
        destination = (row.get("Destination") or "").strip()
        description = row.get("Description") or ""
        country = (row.get("Country") or "").strip().upper()

        activity_value: float = 0.0
        activity_unit = ""
        factor: EmissionFactor | None = None

        if ttype == "FLIGHT":
            cabin, cabin_flag = _normalize_cabin(row.get("Class", ""))
            if cabin_flag:
                flag_reason = _merge_flag(flag_reason, cabin_flag)
            if _is_multileg(description):
                flag_reason = _merge_flag(
                    flag_reason, "multi-leg route, distance may be under-estimated"
                )

            distance = route_distance_km(origin, destination)
            if distance is None:
                flag_reason = _merge_flag(
                    flag_reason,
                    f"unknown airport code(s) origin='{origin}' destination='{destination}'",
                )
                activity_value = 0.0
                activity_unit = "km"
            else:
                activity_value = distance * FLIGHT_ROUTING_UPLIFT
                activity_unit = "km"
                category = "flight_business" if cabin == "business" else "flight_economy"
                factor = find_factor(category, "km", activity_date.year)
                if factor is None:
                    flag_reason = _merge_flag(
                        flag_reason, f"no factor for {category}/{activity_date.year}"
                    )

        elif ttype == "HOTEL":
            try:
                nights = float((row.get("Nights") or "0").strip() or 0)
            except ValueError:
                nights = 0.0
                flag_reason = _merge_flag(flag_reason, "unparseable Nights")
            activity_value = nights
            activity_unit = "night"
            category = f"hotel_{country}" if country else ""
            factor = find_factor(category, "night", activity_date.year) if category else None
            if factor is None:
                flag_reason = _merge_flag(
                    flag_reason, f"no hotel factor for country='{country}'"
                )

        elif ttype == "CAR":
            activity_value = _car_days(row)
            activity_unit = "day"
            factor = find_factor("car_rental", "day", activity_date.year)
            if factor is None:
                flag_reason = _merge_flag(flag_reason, "no car_rental factor seeded")

        elif ttype == "RAIL":
            distance = route_distance_km(origin, destination)
            if distance is None:
                flag_reason = _merge_flag(
                    flag_reason,
                    f"unknown station code(s) origin='{origin}' destination='{destination}'",
                )
                activity_value = 0.0
                activity_unit = "km"
            else:
                activity_value = distance
                activity_unit = "km"
                factor = find_factor("rail", "km", activity_date.year)
                if factor is None:
                    flag_reason = _merge_flag(flag_reason, "no rail factor seeded")

        elif ttype == "TAXI":
            flag_reason = _merge_flag(
                flag_reason, "no route, spend-based estimation needed"
            )
            activity_unit = ""

        else:
            if not origin and not destination and ttype not in ("HOTEL", "CAR"):
                flag_reason = _merge_flag(
                    flag_reason, "no route, spend-based estimation needed"
                )
            else:
                flag_reason = _merge_flag(flag_reason, f"unsupported travel type '{ttype}'")

        co2e_kg = (
            activity_value * factor.factor_value
            if factor is not None and activity_value
            else None
        )

        status = "FLAGGED" if flag_reason else "CLEAN"
        norm = NormalizedRecord.objects.create(
            tenant=batch.tenant,
            raw_record=raw,
            source="TRAVEL",
            scope=3,
            activity_value=activity_value,
            activity_unit=activity_unit,
            activity_date=activity_date,
            emission_factor=factor,
            co2e_kg=co2e_kg,
            review_status=status,
            flag_reason=flag_reason,
        )
        _audit_create(norm, who)
        created.append(norm)

    batch.row_count = len(rows)
    batch.save(update_fields=["row_count"])
    return created


INGESTORS = {
    "SAP": ingest_sap,
    "UTILITY": ingest_utility,
    "TRAVEL": ingest_travel,
}


def ingest(batch: UploadBatch, file_bytes: bytes, who: str) -> list[NormalizedRecord]:
    fn = INGESTORS.get(batch.source)
    if fn is None:
        raise ValueError(f"no ingestor registered for source={batch.source}")
    return fn(batch, file_bytes, who)
