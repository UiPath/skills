# Process Design Document — Retail Account Onboarding

**Organisation:** Fjordline Savings Bank (fictional)
**Department:** Retail Banking Operations
**Process owner:** Retail Banking Operations lead
**Status:** Approved for automation — v1.2

> Fictional, reduced PDD for an evaluation fixture. Names, systems, and figures
> are illustrative only.

## 1. Purpose and scope

Fjordline opens roughly 2,400 retail current accounts a month. About a third of
applications still stall in manual back-office steps between the online form and
the account being live. This PDD covers the as-is process and the target
automated flow for **retail current accounts and retail current accounts with an
overdraft**.

**Out of scope:**

- Wealth-management and private-banking onboarding. Relationship managers run it
  separately in the bank's private-banking platform, Avaloq, and it is not part
  of this automation.
- The periodic KYC refresh for existing customers (a separate initiative).

## 2. Systems used

These are the systems the in-scope process touches. No other system is involved.

| System | Version | Role in the process |
|---|---|---|
| Microsoft Dynamics 365 | 9.2 | CRM — receives the web application and holds the case |
| Signicat | 2026 | Identity document OCR and validation |
| Trapets | 4.1 | KYC and sanctions screening |
| Scrive | 2026 | E-signature of terms and disclosures |
| Temenos T24 | R21 | Core banking — account provisioning |

## 3. As-is process

1. The customer submits the online application; it lands in Microsoft Dynamics 365.
2. A back-office agent opens the case and sends the ID documents to Signicat.
3. The agent submits KYC and sanctions screening to Trapets and polls the alert
   queue by hand. A potential match waits until someone notices it.
4. For overdraft requests only, the agent runs an affordability check.
5. The agent generates terms and sends them through Scrive, then checks by hand
   whether the signature came back.
6. The agent keys the account into Temenos T24. Roughly 5–10% of first attempts
   fail and are retried manually.

**Pain points:** manual polling of Trapets alerts (adds 1–3 days), manual
signature chasing, and re-keying into T24.

## 4. To-be process

1. Dynamics 365 raises an event when an application arrives.
2. Signicat validation and Trapets screening run in parallel.
3. A potential Trapets match becomes a task in the compliance queue; if KYC is not
   completed within 48 hours it escalates automatically to the compliance manager.
4. Approved applications get terms generated and sent through Scrive; a missing
   signature after 7 days abandons the application.
5. The account is provisioned in Temenos T24 with up to three automatic retries,
   then escalates to IT operations.

## 5. Business rules

| Rule | Detail |
|---|---|
| KYC SLA | Verification completes within 48 hours or escalates to the compliance manager |
| Signature window | 7 days, then the application is abandoned |
| Provisioning retries | At most 3 attempts against Temenos T24, then IT-ops escalation |
| Credit data | Pulled only when the customer requested an overdraft |

## 6. Volumes and benefits

| Metric | Value |
|---|---|
| Applications per month | ~2,400 |
| Average handling time today | 38 minutes per application |
| Target handling time | under 5 minutes of human effort |
| Expected end-to-end cycle time | from 4–6 days to under 1 day |

## 7. Exceptions

- Potential sanctions match — human review in the compliance queue.
- Unreadable ID document — the customer is asked to re-upload.
- T24 provisioning failure after retries — IT-ops ticket.
