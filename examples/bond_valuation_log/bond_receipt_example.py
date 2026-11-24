"""One fixed-rate bond: use FinancePy's ValuationLog to inspect a receipt."""
from dataclasses import dataclass, replace
from math import isclose

from financepy.market.curves.flat_discount_curve import FlatDiscountCurve
from financepy.products.bonds.bond import Bond
from financepy.utils.date import Date
from financepy.utils.day_count import DayCountTypes
from financepy.utils.frequency import FrequencyTypes
from financepy.utils.valuation_log import ValuationLog, log_section, log_value


@dataclass(frozen=True)
class Receipt:
    # ISO payment dates and cash per 100 face, with principal in the final flow.
    flows: tuple
    accrued: float
    clean: float
    dirty: float


def make_receipt():
    maturity = Date(15, 1, 2026)
    settlement = Date(15, 4, 2025)
    bond = Bond(
        Date(15, 1, 2024), maturity, 0.06,
        FrequencyTypes.SEMI_ANNUAL, DayCountTypes.THIRTY_E_360,
    )
    curve = FlatDiscountCurve(settlement, 0.0)
    coupon = bond.par * bond.cpn / bond.freq
    # This synthetic example has no ex-dividend interval or adjusted dates.
    flows = tuple(
        (f"{payment.y:04d}-{payment.m:02d}-{payment.d:02d}",
         coupon + (bond.par if accrual == maturity else 0.0))
        for accrual, payment in zip(bond.cpn_dts, bond.payment_dts)
        if accrual > settlement
    )
    return Receipt(
        flows,
        float(bond.accrued_interest(settlement, bond.par)),
        float(bond.clean_price_from_discount_curve(settlement, curve)),
        float(bond.dirty_price_from_discount_curve(settlement, curve)),
    )


def first_difference(expected, observed):
    """Attribute the first observable mismatch, not its underlying cause."""
    def same(left, right):
        return isclose(left, right, rel_tol=0.0, abs_tol=1e-10)

    if len(expected.flows) != len(observed.flows) or any(
        a_dt != b_dt or not same(a_amount, b_amount)
        for (a_dt, a_amount), (b_dt, b_amount) in zip(
            expected.flows, observed.flows
        )
    ):
        return "schedule"
    if not same(expected.accrued, observed.accrued):
        return "accrual"
    if not (same(expected.clean, observed.clean) and
            same(expected.dirty, observed.dirty)):
        return "pricing"
    return "none"


def report(expected, observed):
    """Use the project logger; the checked bond has no logging hooks."""
    with ValuationLog() as log:
        log_section("Fixed-rate bond reconciliation (amounts per 100 face)")
        log_value("Expected flows", expected.flows, "Observed flows", observed.flows)
        log_value("Expected accrued", expected.accrued, "Observed accrued", observed.accrued)
        log_value("Expected clean", expected.clean, "Observed clean", observed.clean)
        log_value("Expected dirty", expected.dirty, "Observed dirty", observed.dirty)
        log_value("First difference", first_difference(expected, observed))
    return log


def planted_accrual_error(receipt):
    # Same dirty price and clean + accrued = dirty, but the accrual is wrong.
    return replace(receipt, accrued=receipt.accrued + 0.25,
                   clean=receipt.clean - 0.25)


if __name__ == "__main__":
    receipt = make_receipt()
    report(receipt, planted_accrual_error(receipt)).print(show_methods=False)
