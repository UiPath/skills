"""What the billing-dispute graders share about the tenant's Billing Dispute SOP."""

import re

# A rule named by section ("§5.4", "SOP 5.4", "section 7") or by title ("Incorrect rate").
NAMES_A_RULE = re.compile(
    r"§\s*\d|\b(?:section|sec\.?|clause|rule|SOP)\s*#?\s*\d+(?:\.\d+)*|\bincorrect[\s-]+rate\b", re.I)
