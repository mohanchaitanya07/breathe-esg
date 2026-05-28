# Data Model For the project

## The Core idea I followed: raw data and normalized data are separate

# rawrecord and normalizedrecord

I designed the model around one main rule that is never lose what the client originally sent.(Because we should not loose what we got initially)

Every uploaded row is stored in two layers:

- `RawRecord`: the original CSV row, stored as JSON.(initial document)
- `NormalizedRecord`: the cleaned and calculated version that analysts review.

The link between these two tables is the audit chain.And This is important because emissions data may later be reviewed by auditors.

## Models

### 1-Tenant

`Tenant` is the multi-tenant root. Each client company gets its own tenant, for example `ACME-001` or `GLOBEX-002`.(these two were there in website already as two different clients)

Uploads, raw records, and normalized records all carry a tenant reference.

### 2-UploadBatch

`UploadBatch` represents one CSV upload.

It stores the tenant, source type, filename, uploader, upload time, and row count. This lets us answer basic provenance questions like: which file created this data, who uploaded it, and when. so we can get to know this data.

### 3-RawRecord

`RawRecord` stores the original CSV row exactly as received.

I used a JSON field because SAP, utility, and travel files all have different columns. For auditability, this row should be treated as write-once source data.

### 4-NormalizedRecord

`NormalizedRecord` is the main reviewable emissions row.

It stores:

- source: `SAP`, `UTILITY`, or `TRAVEL`
- scope: Scope 1, 2, or 3
- normalized activity value and unit
- activity date
- emission factor used
- calculated `co2e_kg`
- review status
- flag reason
- locked state after approval

I kept `source` and `scope` as separate fields because they are not the same thing.
For example, SAP can produce Scope 1 fuel rows and Scope 3 procurement rows. Travel is Scope 3, while utility electricity is Scope 2.

### 5-EmissionFactor

`EmissionFactor` stores the conversion factors, such as diesel kg CO2e per litre or grid electricity kg CO2e per kWh.

Each factor has a category, unit, value, citation, and valid year. I chose to store factors in the database instead of hardcoding them so the calculation can be traced and factors can be updated year by year.

### 6-AuditEntry

`AuditEntry` records what happened to a normalized row.

The current app creates audit entries when rows are ingested and when analysts approve or reject rows. The model also supports future edit tracking through fields like changed field, old value, new value, changed by, and note.so in this way we can know who changed and what are old and new values.

## How the model handles the assignment requirements

- Multi-tenancy: tenant foreign keys on uploaded, raw, and normalized data.
- Scope 1/2/3: stored directly on `NormalizedRecord`.
- Source of truth: `RawRecord` keeps the original row, and `NormalizedRecord` links back to it.
- Source tracking: `UploadBatch` stores file, uploader, time, and source type.
- Unit normalization: normalized activity value and unit are stored on `NormalizedRecord`.
- Audit trail: `AuditEntry` records creation and review actions.

## Traceability chain

So all the reviewed emissions row can be traced like this:

NormalizedRecord -> RawRecord -> UploadBatch -> Tenant

SO THIS chain is the reason I split the model instead of using one large table. One table would be simpler, but it would mix original client data, computed data, and analyst decisions. I kept those separate because auditability matters more than saving a few joins.
