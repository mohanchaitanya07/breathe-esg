from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .ingestion import INGESTORS, ingest
from .models import AuditEntry, NormalizedRecord, Tenant, UploadBatch
from .serializers import NormalizedRecordSerializer


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def upload(request):
    tenant_id = request.data.get("tenant_id")
    source = (request.data.get("source") or "").upper()
    uploaded_by = request.data.get("uploaded_by") or "anonymous"
    upload_file = request.FILES.get("file")

    if not tenant_id:
        return Response({"error": "tenant_id is required"}, status=400)
    if source not in INGESTORS:
        return Response(
            {"error": f"source must be one of {list(INGESTORS)}"}, status=400
        )
    if upload_file is None:
        return Response({"error": "file is required (multipart field 'file')"}, status=400)

    tenant = get_object_or_404(Tenant, pk=tenant_id)

    file_bytes = upload_file.read()

    with transaction.atomic():
        batch = UploadBatch.objects.create(
            tenant=tenant,
            source=source,
            filename=upload_file.name,
            uploaded_by=uploaded_by,
        )
        records = ingest(batch, file_bytes, who=uploaded_by)

    clean = sum(1 for r in records if r.review_status == "CLEAN")
    flagged = sum(1 for r in records if r.review_status == "FLAGGED")
    return Response(
        {
            "batch_id": batch.id,
            "source": batch.source,
            "filename": batch.filename,
            "total": len(records),
            "clean": clean,
            "flagged": flagged,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def list_records(request):
    tenant_id = request.query_params.get("tenant_id")
    if not tenant_id:
        return Response({"error": "tenant_id is required"}, status=400)

    qs = (
        NormalizedRecord.objects
        .filter(tenant_id=tenant_id)
        .select_related("raw_record", "emission_factor")
        .order_by("-created_at")
    )

    source = request.query_params.get("source")
    if source:
        qs = qs.filter(source=source.upper())

    review_status = request.query_params.get("status")
    if review_status:
        qs = qs.filter(review_status=review_status.upper())

    batch_id = request.query_params.get("batch_id")
    if batch_id:
        qs = qs.filter(raw_record__batch_id=batch_id)

    serializer = NormalizedRecordSerializer(qs, many=True)
    return Response({"count": qs.count(), "results": serializer.data})


def _transition(record_id: int, request, action: str, new_status: str, lock: bool):
    record = get_object_or_404(NormalizedRecord, pk=record_id)
    if record.is_locked:
        return Response(
            {"error": "record is locked and cannot be modified"}, status=409
        )

    changed_by = request.data.get("changed_by") or "anonymous"
    note = request.data.get("note") or ""

    old_status = record.review_status
    with transaction.atomic():
        record.review_status = new_status
        record.is_locked = lock
        record.save(update_fields=["review_status", "is_locked"])
        AuditEntry.objects.create(
            normalized_record=record,
            action=action,
            field_changed="review_status",
            old_value=old_status,
            new_value=new_status,
            changed_by=changed_by,
            note=note,
        )

    return Response(NormalizedRecordSerializer(record).data)


@api_view(["POST"])
def approve(request, record_id: int):
    return _transition(record_id, request, action="APPROVED", new_status="APPROVED", lock=True)


@api_view(["POST"])
def reject(request, record_id: int):
    return _transition(record_id, request, action="REJECTED", new_status="REJECTED", lock=False)
