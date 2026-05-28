from django.contrib import admin

from .models import (
    AuditEntry,
    EmissionFactor,
    NormalizedRecord,
    RawRecord,
    Tenant,
    UploadBatch,
)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    search_fields = ("name", "slug")


@admin.register(UploadBatch)
class UploadBatchAdmin(admin.ModelAdmin):
    list_display = ("tenant", "source", "filename", "uploaded_by", "row_count", "uploaded_at")
    list_filter = ("source", "tenant")
    search_fields = ("filename", "uploaded_by")


@admin.register(RawRecord)
class RawRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "batch", "row_number", "created_at")
    list_filter = ("tenant", "batch")

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ()
        return ("tenant", "batch", "row_number", "raw_data", "created_at")


@admin.register(EmissionFactor)
class EmissionFactorAdmin(admin.ModelAdmin):
    list_display = ("category", "unit", "factor_value", "valid_year", "source_citation")
    list_filter = ("valid_year", "unit")
    search_fields = ("category", "source_citation")


@admin.register(NormalizedRecord)
class NormalizedRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tenant",
        "source",
        "scope",
        "activity_value",
        "activity_unit",
        "activity_date",
        "co2e_kg",
        "review_status",
        "is_locked",
    )
    list_filter = ("source", "scope", "review_status", "is_locked", "tenant")
    search_fields = ("flag_reason",)


@admin.register(AuditEntry)
class AuditEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "normalized_record", "action", "field_changed", "changed_by", "changed_at")
    list_filter = ("action",)
    search_fields = ("changed_by", "field_changed", "note")

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ()
        return (
            "normalized_record",
            "action",
            "field_changed",
            "old_value",
            "new_value",
            "changed_by",
            "changed_at",
            "note",
        )
