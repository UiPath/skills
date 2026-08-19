# Card Transaction Dispute — Process Requirements

## What this process is

When a cardholder spots a charge on their statement that they don't recognize or that looks wrong, they can dispute it with their bank. This process handles that dispute from the moment it's raised until it's fully resolved — the cardholder gets their money back, the charge is upheld, or the cardholder drops the dispute (for example, because the merchant refunded them directly).

Every dispute gets its own reference number (e.g. `DSP-001`, `DSP-002`) so everyone involved can track it.

## How a dispute begins

A dispute starts when a cardholder raises one. Along with the dispute, they provide:

- Their name and email
- The card the charge appeared on (last four digits)
- The transaction: date, amount, currency, and the merchant's name
- Why they're disputing it (Unauthorized charge, Duplicate charge, Wrong amount, Goods or services not received, or Other)
- A written description of what happened
- Anything that backs up their claim (receipts, order confirmations, emails with the merchant)
- The date they raised it

At any point while the dispute is open, the cardholder and the people handling it can add more evidence and leave comments on the dispute.

## How fast things should move

A dispute should be fully resolved within **10 business days** of being raised — the cardholder is out of pocket while it's open. Each phase of the process has its own target too:

| Phase | Target |
|---|---|
| Checking the dispute | 1 business day |
| Dispute analyst review | 4 business days |
| Senior review | 2 business days |
| Refunding the cardholder | 2 business days |
| Wrapping up (refunded, upheld, or dropped) | 1 business day |

If a phase is running out of time — say it's used up 70% of its target — the people handling the dispute should see a warning so they can act before the deadline passes.

If a phase misses its deadline entirely, the process doesn't just show it — it acts on its own:

- The dispute is escalated: the disputes team lead gets a task to step in and unblock it.
- The cardholder gets a status update acknowledging the delay.

And if the dispute misses its overall 10-day target, the team lead also gets a make-it-right task to call the cardholder personally before the dispute closes.

## How a dispute moves through the process

### 1. Checking the dispute

When a dispute first comes in, it gets a once-over before anyone spends time investigating:

- The dispute details are checked: Does the transaction actually appear on the account? Was it raised within the allowed dispute window (60 days of the statement)? Is anything missing? Is supporting evidence attached? If something's wrong, the problems are noted so they can be fixed.
- The cardholder's records are pulled up: their account standing, card status, past disputes, and which dispute analyst handles their account.
- The description and evidence are read to confirm the dispute reason matches what the cardholder selected — and to flag anything that looks odd. (This is a helpful extra, not a must.)

The cardholder can add more evidence at any time during this phase.

Once everything checks out, the dispute moves to the analyst. If the cardholder drops the dispute, it skips ahead to the dropped wrap-up.

One more thing: if the analyst later needs more from the cardholder and sends the dispute back (see next phase), the dispute comes **back to this phase** and goes through these checks again.

### 2. Dispute analyst review

The dispute now goes to the analyst assigned to this cardholder's account:

- The analyst gets an email with a summary of the dispute and links to uphold or decline it.
- The merchant is asked to respond to the dispute, and the dispute then waits for the merchant's reply.
- The analyst weighs the cardholder's evidence against the merchant's response, adds their comments, and makes a call: the cardholder's claim holds up (send it on for a refund decision), the merchant's proof is solid (uphold the charge), or more is needed from the cardholder (send it back).
- If the analyst sits on it too long, the dispute automatically gets bumped up to a senior analyst so it doesn't stall.
- While reviewing, the analyst can also contact the cardholder to ask for clarification or extra evidence — whenever they need to.

From here, the dispute can go four ways:

- **Analyst finds the claim holds up** → the dispute moves on to senior review.
- **Analyst finds the charge is valid** → the dispute goes to the upheld wrap-up.
- **Analyst sends it back for more evidence** → the dispute returns to "Checking the dispute."
- **Cardholder drops it** → the dispute goes to the dropped wrap-up.

### 3. Senior review

Before any money is returned, the dispute gets a deeper look:

- The dispute is checked against the bank's rules: Has this same charge been disputed before? How many disputes has this account raised recently? Does the claim comply with the card network's dispute rules? This produces a risk score and flags anything of concern.
- The dispute is compared against past dispute patterns to spot warning signs of abuse — for example, an account that disputes charges regularly, or claims about goods "not received" that the merchant shows were delivered. (This is a helpful extra, not a must.)
- The amount determines who needs to sign off: disputes under $50 are refunded automatically, disputes under $500 only need the analyst's earlier finding, and disputes of $500 or more need a senior reviewer's sign-off.
- A senior reviewer then sees the whole picture — the dispute, both sides' evidence, and the risk score — and makes the final decision. **The dispute waits for them to explicitly choose what happens next**: refund the cardholder, or uphold the charge. It never moves forward on its own from here.

If the reviewer upholds the charge, the dispute goes to the upheld wrap-up. The cardholder can still drop the dispute during this phase too.

### 4. Refunding the cardholder

Once a senior reviewer sends the dispute to refund:

- A credit for the disputed amount is posted back to the cardholder's account.
- Optionally, a separate recovery record is opened to claw the money back from the merchant's bank, linked back to this dispute, so that recovery can be followed on its own.
- The dispute waits for confirmation that the credit has landed on the account, then the refund is marked complete.

If the credit posts successfully, the dispute moves to the refunded wrap-up. If it fails — the account has since been closed, or there's a fraud hold on it — the dispute goes to the upheld wrap-up instead, where the cardholder is told what happened and how to follow up.

### 5. Wrap-up: Cardholder refunded

The happy ending. Two final things happen, and then the dispute is closed:

- The cardholder gets a confirmation message with the refunded amount, a reference number, and when it will show on their statement.
- The refund is recorded in the bank's books against the account and the original transaction.

Once a dispute reaches this point, it's done — it can't move anywhere else.

### 6. Wrap-up: Charge upheld

A charge can be upheld by the analyst, by the senior reviewer, or because the refund couldn't be posted. When that happens:

- The cardholder gets an explanation of why the charge stands, who made the decision, and what they can do next — provide new evidence and re-dispute, or escalate.
- The decision is logged for the bank's audit records — what was upheld, by whom, why, and when.

Then the dispute is closed. It can't move anywhere else.

### 7. Wrap-up: Dispute dropped

The cardholder can drop the dispute at any point before a refund is issued — while it's being checked, while the analyst has it, or while it's in senior review — typically because the merchant sorted it out with them directly. When they do:

- The cardholder gets a confirmation that the dispute has been closed at their request.
- Anything still in motion is tidied up: pending reviews are cancelled, the merchant inquiry is closed, countdown timers are switched off, and the dispute is marked dropped.

Then the dispute is closed. It can't move anywhere else.

## Actions people can take at any time

Beyond the sequenced steps above, the people on a dispute must be able to take these actions whenever they judge it necessary, at any point while the dispute is in one of the three active phases:

- **Add to the dispute** — the cardholder and handlers can attach evidence and leave comments.
- **Ask the cardholder a question** — any handler can request clarification or extra evidence.
- **Order a fraud team check** — any handler who senses something off can ask the fraud team to look at the account; their findings are added to the dispute for the next decision-maker to see.
- **Pull in a manager** — even when the amount doesn't require it, a handler who is uneasy can ask a manager to review and sign off; the dispute waits for that opinion before moving on.
- **Drop the dispute** — the cardholder can drop it (as described in the phases above).

## Things this process must handle

- **Going backwards** — the analyst can send a dispute back for more evidence, and it goes through the initial checks again before returning to review.
- **Dropping at any time** — the cardholder can drop the dispute during any of the three active phases, and everything wraps up cleanly.
- **No stalling** — a review that sits untouched gets escalated automatically.
- **Deadlines that act** — reaching 70% of a target warns people; missing the deadline triggers real work on its own (an escalation task for the team lead, a status note to the cardholder), not just a visual change.
- **A person decides the path** — after senior review, the dispute never advances by itself; it waits for the reviewer's explicit choice.
- **Side-by-side tracking** — recovering the money from the merchant can be followed through its own linked record without holding up or cluttering the main dispute.
- **On-demand actions** — the actions under "Actions people can take at any time" aren't steps in a sequence; a handler can order a fraud check or pull in a manager whenever their judgment says so, and the dispute waits where it needs to.

## When we'd call this done

The process should be able to carry a dispute through every path end to end:

- A dispute that ends in a refund
- A charge upheld by the analyst, one upheld by the senior reviewer, and one upheld because the refund couldn't be posted
- A dispute the cardholder drops
- A dispute sent back for more evidence, completed, and resubmitted through to a decision

And once a dispute is closed — refunded, upheld, or dropped — nothing can reopen or move it.

