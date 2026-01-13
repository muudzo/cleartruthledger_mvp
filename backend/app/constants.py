from enum import Enum

class LedgerEventType(str, Enum):
    POSTING = "POSTING"
    REVERSAL = "REVERSAL"

INITIAL_HASH = "0" * 64

# Account Types or Standard Accounts could go here
# e.g. ACCOUNT_CASH = "CASH"
