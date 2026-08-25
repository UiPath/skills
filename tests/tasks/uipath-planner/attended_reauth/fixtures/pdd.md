# Process Design Document: VAT Return Submission

## Process Overview
- **Process Name:** VAT Return Submission
- **Department:** Finance — Tax
- **Objective:** Submit monthly VAT returns to the national tax authority
  portal and file the acknowledgement receipts.
- **Schedule:** Monthly, first business day
- **Volume:** 40–60 returns per run
- **Exception rate:** ~5%

## In Scope
- Log into the government tax portal
- Upload each prepared VAT return
- Download the acknowledgement PDF for each submission
- File acknowledgements in SharePoint

## Out of Scope
- Preparing the VAT return figures (done upstream in the ERP)
- Dispute / correction handling

## Detailed Process Steps
| Step | Action | Application | Expected Result |
|------|--------|-------------|-----------------|
| 1.1 | A licensed tax officer inserts the hardware security token and completes the portal sign-in with their PIN | Gov Tax Portal | Authenticated portal session |
| 1.2 | Navigate to the VAT filing queue | Gov Tax Portal | Filing queue open |
| 1.3 | For each prepared return, upload the return file | Gov Tax Portal | Return accepted, reference issued |
| 1.4 | Download the acknowledgement PDF | Gov Tax Portal | PDF saved to temp folder |
| 1.5 | File the acknowledgement in the Tax SharePoint library | SharePoint | Acknowledgement archived |

## Application Details
| Application | Interface | Authentication |
|-------------|-----------|----------------|
| Gov Tax Portal | Web | **Physical hardware security token (smart card / USB crypto token) with PIN.** The token is held by a licensed tax officer and cannot be read or supplied by software — a human must complete the sign-in. |
| SharePoint | Web | Service account (credentials in Orchestrator assets) |

## Robot Attendance
A licensed tax officer must be physically present at the machine to complete
the hardware-token sign-in to the tax portal before the run can proceed. The
portal session may also expire during a long run and require the officer to
re-authenticate.

## Notes
This PDD leaves the run schedule window, notification recipients, and the
acknowledgement retention period unspecified.
