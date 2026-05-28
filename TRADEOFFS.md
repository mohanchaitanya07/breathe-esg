# Tradeoffs — Breathe ESG

These are the main things I deliberately did not build for the prototype, and why:

## 1. Real authentication and roles

I did not build a full login system.
The app uses a fixed analyst identity, `analyst@breathe`, and records that identity in the audit trail for uploads and review actions.

Right now i didn't choose to build auth because its not the important part of grading and i focused on whats actually important right now.
Django admin still uses Django's built-in authentication.

## 2. Spend-based procurement emissions

And also I did not calculate emissions for general SAP procurement rows.

Fuel rows are activity-based, so litres or kilograms can be multiplied by a factor. Procurement rows like laptops, packaging, or office supplies usually need spend-based factors, supplier-specific factors, or product category mappings.
I chose to flag those rows instead of inventing numbers. That felt more honest right now.

## 3. Live API integrations

And I did not build SAP OData, Concur, Navan, or utility API integrations.

Because if felt For a new client, CSV is the realistic first path. API access usually needs approvals, credentials, vendor setup, and client IT involvement.

The ingestion code is still separated by source, so these can be added later.
