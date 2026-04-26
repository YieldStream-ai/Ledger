from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from pydantic import BaseModel


class ArithmeticValidation(BaseModel):
    balance_check: str        # "passed" | "failed" | "skipped"
    expected_ending: float
    actual_ending: float
    discrepancy: float
    confidence: float         # 0-1


def _to_decimal(value: float | int | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def validate_arithmetic(parsed_data: dict) -> ArithmeticValidation:
    """Post-processing arithmetic reconciliation check.

    Verifies: beginning_balance + sum(credits) - sum(debits) == ending_balance
    Uses Decimal internally for precision. Tolerance: $0.01.
    """
    beginning = _to_decimal(parsed_data.get("beginning_balance"))
    ending = _to_decimal(parsed_data.get("ending_balance"))

    # Skip if required balances are missing
    if beginning is None or ending is None:
        return ArithmeticValidation(
            balance_check="skipped",
            expected_ending=0.0,
            actual_ending=float(ending) if ending is not None else 0.0,
            discrepancy=0.0,
            confidence=0.0,
        )

    transactions = parsed_data.get("transactions") or []

    if transactions:
        # Primary path: sum individual transactions
        sum_credits = Decimal("0")
        sum_debits = Decimal("0")
        for txn in transactions:
            amt = _to_decimal(txn.get("amount"))
            if amt is None:
                continue
            txn_type = (txn.get("type") or "").lower()
            if txn_type in ("credit", "deposit"):
                sum_credits += amt
            elif txn_type in ("debit", "withdrawal"):
                sum_debits += amt

        expected = beginning + sum_credits - sum_debits
        confidence = 0.99
    else:
        # Fallback: use statement-level totals
        total_deposits = _to_decimal(parsed_data.get("total_deposits"))
        total_withdrawals = _to_decimal(parsed_data.get("total_withdrawals"))

        if total_deposits is None or total_withdrawals is None:
            return ArithmeticValidation(
                balance_check="skipped",
                expected_ending=0.0,
                actual_ending=float(ending),
                discrepancy=0.0,
                confidence=0.0,
            )

        expected = beginning + total_deposits - total_withdrawals
        confidence = 0.85

    tolerance = Decimal("0.01")
    disc = abs(expected - ending)
    passed = disc <= tolerance

    return ArithmeticValidation(
        balance_check="passed" if passed else "failed",
        expected_ending=float(expected.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        actual_ending=float(ending),
        discrepancy=float(disc.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        confidence=confidence,
    )
