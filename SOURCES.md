# Sources — Breathe ESG

This file explains what I assumed about each source, what I modeled in the sample data, and where the prototype would need more work in production.

## 1. SAP: fuel and procurement

I treated SAP data as a flat purchase-order CSV export, similar to what a user might export from ME2N.
I chose this because it is realistic for early onboarding. A client can usually export a CSV before they can give us IDoc, BAPI, or OData access.

What I modeled:

- German-style column names like `Bestellmenge`, `BME`, `Warengruppe`, and `Bestelldatum`
- fuel and procurement rows in the same file
- inconsistent units such as `L`, `KG`, `GAL`, `ST`, and `EA`
- mixed date formats
- material text used to infer fuel type

What would break in production:

- plant code lookups
- non-standard SAP exports
- service purchase orders
- very large exports that need background processing

## 2. Utility electricity

I treated utility data as a portal CSV billing-history export.

I chose this over PDF bills because PDFs vary too much by utility and would require OCR/layout parsing. I also did not assume an API, because many utilities do not provide one.In india many utilities are not providing any apis it seems as per my research.

What I modeled:

- account number
- bill number
- billing period start and end
- kWh usage
- actual vs estimated readings

The main issue I handled is that utility bills often cross calendar months. The app splits kWh across months using daily pro-rata allocation.

I also added review flags for estimated readings and large consumption spikes.

What would break in production:

- multiple meters per site
- estimated bills later corrected by true-up bills
- solar net metering
- demand-based reporting needs
- different utility portal column names

## 3. Corporate travel

I treated travel data as an expense or travel report CSV.

I chose this because Concur/Navan-style APIs usually need admin credentials, OAuth setup, and customer-specific access. CSV is the realistic first file a travel or finance team can share.

What I modeled:

- flights using airport codes
- hotel stays using nights
- car rental using days
- rail trips using route distance where possible
- taxi rows without route data
- cabin class differences for flight factors

For flights, the app derives distance from airport codes and applies a routing uplift. Hotels use country-level factors. Taxi rows are flagged because they need spend-based estimation or route data.

What would break in production:

- multi-leg flights needing segment-level calculation
- unusual cabin class codes
- missing or outdated airport codes
- ride-share and taxi rows without distance

## Sample data

The sample files are synthetic but intentionally shaped like real exports.

I included mostly clean rows and specific edge cases so the review dashboard shows them. Examples include ambiguous dates, missing units, gallons conversion, estimated utility readings, consumption spikes, unknown routes, and spend-based rows that should not be guessed.
