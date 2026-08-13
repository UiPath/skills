# Auto Insurance Claim Settlement — Process Requirements

## What this process is

When a policyholder's car is damaged, they file a claim with their insurance company. This process handles that claim from the moment it's submitted until it's fully resolved — the claimant gets paid, the claim is turned down, or the claimant decides to withdraw it.

Every claim gets its own reference number (e.g. `CLM-001`, `CLM-002`) so everyone involved can track it.

## How a claim begins

A claim starts when a policyholder submits one. Along with the claim, they provide:

- Their name and email
- Their policy number
- What kind of damage it is (Collision, Theft, Weather, Vandalism, or Other)
- How much they're claiming, and in what currency
- A written description of what happened
- Photos and documents that support the claim (damage photos, repair estimates, police reports)
- The date they submitted it

At any point while the claim is open, the claimant and the people handling it can add more documents and leave comments on the claim.

## How fast things should move

A claim should be fully resolved within **10 business days** of being filed. Each phase of the process has its own target too:

| Phase | Target |
|---|---|
| Checking the claim | 1 business day |
| Adjuster review | 3 business days |
| Senior review | 3 business days |
| Paying the claimant | 2 business days |
| Wrapping up (paid, turned down, or withdrawn) | 1 business day |

If a phase is running out of time — say it's used up 70% of its target — the people handling the claim should see a warning so they can act before the deadline passes.

If a phase misses its deadline entirely, the process doesn't just show it — it acts on its own:

- The claim is escalated: the claims team lead gets a task to step in and unblock it.
- The claimant gets a status update apologizing for the delay and giving a new expected date.

And if the claim misses its overall 10-day target, the team lead also gets a service-recovery task to review what went wrong before the claim closes.

## How a claim moves through the process

### 1. Checking the claim

When a claim first arrives, it gets a once-over before anyone spends time reviewing it:

- The claim details are checked: Is the policy active? Is the amount within what the policy covers? Is anything missing? Are photos or documents attached? If something's wrong, the problems are noted so they can be fixed.
- The policyholder's records are pulled up: their policy details, coverage limits, past claims, and which adjuster handles their account.
- The description and photos are read to confirm the type of damage matches what the claimant selected — and to flag anything that looks odd. (This is a helpful extra, not a must.)

The claimant can add more photos or documents at any time during this phase.

Once everything checks out, the claim moves to the adjuster. If the claimant changes their mind and withdraws, the claim skips ahead to the withdrawal wrap-up.

One more thing: if the adjuster later finds problems and sends the claim back for corrections (see next phase), the claim comes **back to this phase** and goes through these checks again.

### 2. Adjuster review

The claim now goes to the adjuster assigned to this policyholder:

- The adjuster gets an email with a summary of the claim and links to approve or decline it.
- The claim then waits for the adjuster to respond.
- The adjuster looks over the full claim, adds their comments, and makes a call: approve it, decline it, or send it back to the claimant to fix something.
- If the adjuster sits on it too long, the claim automatically gets bumped up to a senior adjuster so it doesn't stall.
- While reviewing, the adjuster can also email the claimant to ask for clarification or missing paperwork — whenever they need to.

From here, the claim can go four ways:

- **Adjuster approves** → the claim moves on to senior review.
- **Adjuster declines** → the claim goes to the turn-down wrap-up.
- **Adjuster sends it back for corrections** → the claim returns to "Checking the claim."
- **Claimant withdraws** → the claim goes to the withdrawal wrap-up.

### 3. Senior review

Before any money goes out, the claim gets a deeper look:

- The claim is checked against company policy: Has this been submitted before? Is there enough coverage left on the policy? Does it comply with the policy's terms? This produces a risk score and flags anything of concern.
- The claim is compared against past claim patterns to spot warning signs of fraud — for example, several recent claims on the same policy, amounts that sit just under approval limits, or unusual timing. (This is a helpful extra, not a must.)
- The company confirms funds are available, and the right level of sign-off is determined by the amount: claims under $500 are approved automatically, claims under $5,000 only need the adjuster's earlier approval, and claims of $5,000 or more need a senior reviewer's sign-off.
- A senior reviewer then sees the whole picture — the claim, the compliance results, and the risk score — and makes the final decision. **The claim waits for them to explicitly choose what happens next**: send it to payment, or turn it down. It never moves forward on its own from here.

If the reviewer turns it down, the claim goes to the turn-down wrap-up. The claimant can still withdraw during this phase too.

### 4. Paying the claimant

Once a senior reviewer sends the claim to payment:

- A payment for the approved amount is set up and sent to the claimant's bank account.
- Optionally, a separate tracking record is opened just for following the payout, linked back to the claim, so the payment can be followed on its own.
- The claim waits for the bank to confirm the money went through, then the payment is marked complete.

If the payment goes through, the claim moves to the "paid" wrap-up. If the payment fails — wrong bank details, or a fraud hold — the claim goes to the turn-down wrap-up instead.

### 5. Wrap-up: Claim paid

The happy ending. Two final things happen, and then the claim is closed:

- The claimant gets a confirmation message with the amount, a payment reference, and when to expect the deposit.
- The payout is recorded in the company's books against the policy.

Once a claim reaches this point, it's done — it can't move anywhere else.

### 6. Wrap-up: Claim turned down

A claim can be turned down by the adjuster, by the senior reviewer, or because payment failed. When that happens:

- The claimant gets an email explaining why it was turned down, who made the decision, and how to resubmit or appeal.
- The decision is logged for the company's audit records — what was turned down, by whom, why, and when.

Then the claim is closed. It can't move anywhere else.

### 7. Wrap-up: Claim withdrawn

The claimant can withdraw their claim at any point before payment — while it's being checked, while the adjuster has it, or while it's in senior review. When they do:

- The claimant gets an email confirming the withdrawal.
- Anything still in motion is tidied up: pending reviews are cancelled, countdown timers are switched off, and the claim is marked withdrawn.

Then the claim is closed. It can't move anywhere else.

## Actions people can take at any time

Beyond the sequenced steps above, the people on a claim must be able to take these actions whenever they judge it necessary, at any point while the claim is in one of the three active phases:

- **Add to the claim** — the claimant and handlers can attach documents and leave comments.
- **Ask the claimant a question** — any handler can email the claimant for clarification or missing paperwork.
- **Order a second opinion** — any handler who wants extra certainty can order an independent damage inspection from someone not already involved in the claim; the findings are added to the claim for the next decision-maker to see.
- **Pull in a manager** — even when the amount doesn't require it, a handler who is uneasy about a claim can ask a manager to look at it and give a sign-off; the claim waits for that opinion before moving on.
- **Withdraw** — the claimant can withdraw the claim (as described in the phases above).

## Things this process must handle

- **Going backwards** — the adjuster can send a claim back for corrections, and it goes through the initial checks again before returning to review.
- **Withdrawing at any time** — the claimant can pull out during any of the three active phases, and everything wraps up cleanly.
- **No stalling** — a review that sits untouched gets escalated automatically.
- **Deadlines that act** — reaching 70% of a target warns people; missing the deadline triggers real work on its own (an escalation task for the team lead, a delay notice to the claimant), not just a visual change.
- **A person decides the path** — after senior review, the claim never advances by itself; it waits for the reviewer's explicit choice.
- **Side-by-side tracking** — the payout can be followed through its own linked tracking record without holding up or cluttering the main claim.
- **On-demand actions** — the actions under "Actions people can take at any time" aren't steps in a sequence; a handler can order a second opinion or pull in a manager whenever their judgment says so, and the claim waits where it needs to.

## When we'd call this done

The process should be able to carry a claim through every path end to end:

- A claim that gets paid
- A claim turned down by the adjuster, one turned down by the senior reviewer, and one turned down because the payment failed
- A claim the claimant withdraws
- A claim sent back for corrections, fixed, and resubmitted through to a decision

And once a claim is closed — paid, turned down, or withdrawn — nothing can reopen or move it.

