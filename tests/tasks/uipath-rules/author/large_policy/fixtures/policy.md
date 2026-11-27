# Loan underwriting policy

Each heading names one result the process reads. Use the name in backticks as the output name.

## Inputs

| Name | Type |
|---|---|
| `creditScore` | number |
| `income` | number |
| `loanAmount` | number |
| `debtRatio` | number, 0 to 1 |
| `employmentYears` | number |
| `existingCustomer` | boolean |

## Risk band: `riskBand` (string)

- A credit score below 580 is "High".
- A credit score from 580 up to 699 is "Medium" when income is at least 50000, otherwise "High".
- A credit score of 700 or more is "Low".

## Affordability: `affordability` (string)

- A debt ratio of 0.3 or less is "Good".
- A debt ratio above 0.3 and up to 0.45 is "Fair".
- A debt ratio above 0.45 is "Poor".

## Employment stability: `stability` (string)

- Two or more years of employment is "Stable".
- Less than two years is "New".

## Loan size: `loanSize` (string)

- A loan amount below 25000 is "Small".
- A loan amount from 25000 up to 99999 is "Standard".
- A loan amount of 100000 or more is "Large".

## Base rate: `baseRate` (number)

The base rate comes from the risk band and the loan size.

| Risk band | Large loan | Any other size |
|---|---|---|
| "High" | 12.5 | 12.5 |
| "Medium" | 9 | 8 |
| "Low" | 6 | 5.5 |

## Loyalty discount: `loyaltyDiscount` (number)

- An existing customer with "Stable" employment gets 0.5.
- Any other existing customer gets 0.25.
- A new customer gets 0.

## Eligibility: `eligibility` (string)

- A "High" risk band or "Poor" affordability is "Declined".
- A "Medium" risk band with "Fair" affordability is "Review".
- Everything else is "Eligible".

## Approval route: `approvalRoute` (string)

- A "Declined" application is "Reject".
- A "Review" application, a "Large" loan, or "New" employment is "Manual".
- Everything else is "Auto".
