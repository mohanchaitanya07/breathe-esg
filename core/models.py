from django.db import models


SOURCE_CHOICES = [
    ("SAP", "SAP (fuel + procurement)"),
    ("UTILITY", "Utility (electricity)"),
    ("TRAVEL", "Travel (flights/hotels/cars)"),
]

SCOPE_CHOICES = [
    (1, "Scope 1 — direct"),
    (2, "Scope 2 — purchased energy"),
    (3, "Scope 3 — value chain"),
]


class Tenant(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class UploadBatch(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="batches")
    source = models.CharField(max_length=16, choices=SOURCE_CHOICES)
    filename = models.CharField(max_length=255)
    uploaded_by = models.CharField(max_length=120)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    row_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.tenant.slug} / {self.source} / {self.filename}"


class RawRecord(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="raw_records")
    batch = models.ForeignKey(UploadBatch, on_delete=models.CASCADE, related_name="raw_records")
    row_number = models.IntegerField()
    raw_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"raw#{self.id} batch={self.batch_id} row={self.row_number}"


class EmissionFactor(models.Model):
    category = models.CharField(max_length=80)
    unit = models.CharField(max_length=20)
    factor_value = models.FloatField(help_text="kg CO2e per unit of activity")
    source_citation = models.CharField(max_length=200)
    valid_year = models.IntegerField()

    def __str__(self):
        return f"{self.category} ({self.unit}) {self.valid_year} = {self.factor_value} kgCO2e"


class NormalizedRecord(models.Model):
    REVIEW_STATUS_CHOICES = [
        ("CLEAN", "Clean — no issues detected"),
        ("FLAGGED", "Flagged — needs analyst attention"),
        ("APPROVED", "Approved — ready for audit"),
        ("REJECTED", "Rejected — excluded from reporting"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="normalized_records")
    raw_record = models.ForeignKey(
        RawRecord, on_delete=models.CASCADE, related_name="normalized_records"
    )

    source = models.CharField(max_length=16, choices=SOURCE_CHOICES)
    scope = models.IntegerField(choices=SCOPE_CHOICES)

    activity_value = models.FloatField()
    activity_unit = models.CharField(max_length=20)
    activity_date = models.DateField()

    emission_factor = models.ForeignKey(
        EmissionFactor, on_delete=models.SET_NULL, null=True, blank=True
    )
    co2e_kg = models.FloatField(null=True, blank=True)

    review_status = models.CharField(
        max_length=16, choices=REVIEW_STATUS_CHOICES, default="CLEAN"
    )
    flag_reason = models.CharField(max_length=255, blank=True)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"norm#{self.id} {self.source}/S{self.scope} "
            f"{self.activity_value}{self.activity_unit} [{self.review_status}]"
        )


class AuditEntry(models.Model):
    ACTION_CHOICES = [
        ("CREATED", "Created"),
        ("EDITED", "Edited"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    normalized_record = models.ForeignKey(
        NormalizedRecord, on_delete=models.CASCADE, related_name="audit_entries"
    )
    action = models.CharField(max_length=16, choices=ACTION_CHOICES)
    field_changed = models.CharField(max_length=80, blank=True)
    old_value = models.CharField(max_length=255, blank=True)
    new_value = models.CharField(max_length=255, blank=True)
    changed_by = models.CharField(max_length=120)
    changed_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    def __str__(self):
        return f"audit#{self.id} {self.action} on norm={self.normalized_record_id}"
