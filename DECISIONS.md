# Decisions — Breathe ESG

This file explains the main ambiguities I resolved while building the prototype, what I chose, and what I would ask the PM next.

## I used CSV uploads for all three sources

I chose CSV as the ingestion format for SAP, utility, and travel.

Because For a new enterprise onboarding, API access usually does not happen on day one. It needs IT approval, security review, credentials, and sometimes vendor-specific setup. CSV exports are much more realistic for a prototype because finance, facilities, or sustainability teams can usually get them immediately.SO i have choosen CSVs for all three sources.

The app still has a clean upgrade path: each source has its own ingestor, so an api adapter can be added later.

## SAP decision

For SAP, I modeled a flat purchase-order style CSV, similar to a ME2N export.

I chose this because it is a realistic export shape: German headers, material groups, quantities, units, plant codes, dates, and procurement/fuel rows mixed together.

I did not choose IDoc, BAPI, or OData for the MVP. They are more "enterprise correct", but they require SAP system access and setup that a prototype would not have. A CSV export lets the app show the hard part: messy units, unclear categories, and rows that need analyst review.

Handled:

- fuel rows
- procurement rows
- German-style SAP columns
- litre/gallon conversion
- count-based units that cannot safely produce emissions

Ignored:

- multi-currency conversion
- service purchase orders
- the many extra columns in a real ME2N export

## Utility decision

For utility electricity, I modeled a portal CSV billing-history export.

I chose this because many facilities teams can download CSV or spreadsheet billing history from a utility portal. I avoided PDF bills because every utility layout is different and OCR would become its own project. I also avoided direct APIs because they are not consistently available in indian utility data.

Handled:

- billing period start and end dates
- kWh consumption
- account number
- actual vs estimated readings
- spike detection compared to the account median

Ignored:

- demand charges
- tariff slabs
- power factor billing logic
- solar net metering

## Travel decision

For travel, I modeled an expense/travel report CSV.

I chose this over Concur or Navan APIs because those APIs usually require partner access, tenant OAuth setup, and real customer credentials. CSV is the common fallback across corporate travel platforms.

Handled:

- flights
- hotels
- car rental
- rail
- airport-code distance for flights
- cabin class for economy vs business

Ignored:

- personal vs business filtering
- spend-based taxi estimation

## Scope routing

I stored source and scope separately because they are not the same thing.

The routing I chose:

- SAP material group `300` means fuel, so it becomes Scope 1.
- Other SAP procurement rows become Scope 3, but are flagged because procurement factors are outside this MVP.
- Utility electricity becomes Scope 2.
- Travel becomes Scope 3.

This keeps the logic simple, visible, and easy to defend.

## Utility billing periods

Utility bills often do not match calendar months, but carbon reporting usually needs monthly activity.

I chose daily pro-rata splitting. If a bill covers 30 days and crosses two months, the kWh is split by how many days fall in each month.

This is better than assigning the whole bill to the bill end month, which can distort monthly reporting. It is still an estimate, but it is explainable and works without interval meter data.

## Flagging approach

I chose to flag uncertainty instead of guessing silently.

If a row has an ambiguous date, missing unit, unknown airport code, unsupported unit, estimated reading, or missing factor, the app keeps the row but marks it as needing review.

Clean rows are not automatically final either. They still need analyst approval before they are locked.

## Who uploads files

I built the workflow around the analyst uploading files.

That matches the assignment's focus: analysts need to review, approve, and prepare data for audit. Client self-upload would require a real client authentication and permissions layer, which I treated as a later phase.

## What I would ask the PM

- Should procurement emissions be estimated with spend-based factors now, or is flagging procurement acceptable for the MVP? Like right now can we flag them by saying out of MVP scope?

- Which travel platform does the client actually use? which real platform should we support first?

- What monthly data volume should we expect? How many 500 or 5,00,000 rows?

- Should approval lock rows permanently, or should admins be able to reopen it if there was a mistake?
