from rest_framework import serializers

from .models import NormalizedRecord


class NormalizedRecordSerializer(serializers.ModelSerializer):
    raw_data = serializers.JSONField(source="raw_record.raw_data", read_only=True)
    raw_row_number = serializers.IntegerField(source="raw_record.row_number", read_only=True)
    batch_id = serializers.IntegerField(source="raw_record.batch_id", read_only=True)

    class Meta:
        model = NormalizedRecord
        fields = (
            "id",
            "tenant",
            "source",
            "scope",
            "activity_value",
            "activity_unit",
            "activity_date",
            "co2e_kg",
            "review_status",
            "flag_reason",
            "is_locked",
            "created_at",
            "raw_row_number",
            "batch_id",
            "raw_data",
        )
