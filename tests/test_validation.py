"""The 3 required guardrails. Allowed ₹ figures come from real recorded tool output."""

import pytest

from app.agent.validation import (
    allowed_amounts, check_approval_promise, check_tax_advice, check_unreturned_rupees,
    extract_rupees, validate,
)

USER = ["I spend 15k a month on Amazon. Which card?"]


@pytest.fixture
def amazon(raw):
    return [raw("recommend__amazon_15k")["parsed_content"][0]]


# ---------------- extraction

@pytest.mark.parametrize("text,value", [
    ("₹9,000", 9000), ("₹1,31,219.997", 131219.997), ("Rs. 1,180", 1180), ("Rs 500", 500),
    ("INR 2,500", 2500), ("₹15k", 15000), ("₹1.5 lakh", 150000), ("₹2 L", 200000),
    ("₹1 crore", 1e7), ("5,000 rupees", 5000), ("₹0", 0),
])
def test_extract_formats(text, value):
    got = extract_rupees(f"You get {text} back.")
    assert len(got) == 1 and got[0].value == pytest.approx(value)


def test_non_currency_numbers_ignored():
    assert extract_rupees("5% cashback, 4 lounge visits, 1000 reward points, rank 2") == []


# ---------------- rule 1: unreturned rupee figures

def test_figures_from_tool_pass(amazon):
    ans = "HDFC Millenia: ₹9,000 a year in rewards, joining fee ₹1,180, waived at ₹1,00,000 spend."
    assert check_unreturned_rupees(ans, allowed_amounts(amazon, USER)) == []


def test_rounded_display_passes(amazon):
    assert check_unreturned_rupees("about ₹9k a year", allowed_amounts(amazon, USER)) == []


def test_user_figures_and_annualisation_pass(amazon):
    ans = "On your ₹15,000 monthly Amazon spend (₹1,80,000 a year)..."
    assert check_unreturned_rupees(ans, allowed_amounts(amazon, USER)) == []


def test_model_computed_figure_flagged(amazon):
    # C11: server playbook asks the model for break-even / first-year net; tools never return 7,820
    ans = "After the ₹1,180 joining fee you net ₹7,820 in year one."
    v = check_unreturned_rupees(ans, allowed_amounts(amazon, USER))
    assert [x.snippet for x in v] == ["₹7,820"]


def test_invented_figure_flagged_without_tools():
    v = check_unreturned_rupees("You'd save ₹12,000 a year.", allowed_amounts([], ["hi"]))
    assert len(v) == 1 and v[0].rule == "unreturned_rupee"


def test_lakh_rounding_tolerance():
    allowed = allowed_amounts([{"x": "₹1,31,219.997"}], [])
    assert check_unreturned_rupees("about ₹1.31 lakh", allowed) == []
    assert check_unreturned_rupees("about ₹1.5 lakh", allowed) != []


# ---------------- rule 2: approval promises

@pytest.mark.parametrize("text", [
    "You will definitely get approved for this card.",
    "Approval is guaranteed with your income.",
    "We guarantee approval.",
    "You're pre-approved for the Axis Magnus.",
    "100% approval for salaried users.",
    "You'll be approved easily.",
])
def test_approval_promises_flagged(text):
    assert check_approval_promise(text), text


@pytest.mark.parametrize("text", [
    "Approval is not guaranteed; the bank decides.",
    "I can't guarantee approval.",
    "You appear to meet the listed income criteria, but the bank makes the final decision.",
    "Eligibility shown here does not mean you will be approved.",
])
def test_approval_hedges_pass(text):
    assert check_approval_promise(text) == [], text


# ---------------- rule 3: tax advice

@pytest.mark.parametrize("text", [
    "Paying insurance with this card helps you save tax under Section 80D.",
    "The annual fee is tax-deductible under 80C.",
    "You can claim the fee as a business expense to reduce your taxable income.",
    "This gives you a tax benefit too.",
])
def test_tax_advice_flagged(text):
    assert check_tax_advice(text), text


@pytest.mark.parametrize("text", [
    "I can't give tax advice; please consult a chartered accountant about Section 80D.",
    "The joining fee is ₹1,180 including 18% GST.",
    "Rent payments earn 1% cashback.",
])
def test_tax_non_advice_passes(text):
    assert check_tax_advice(text) == [], text


# ---------------- combined

def test_validate_combined(amazon):
    ans = "Get HDFC Millenia, you'll definitely get approved, and you'll net ₹7,820. It also helps you save tax."
    rep = validate(ans, amazon, USER)
    assert not rep.ok
    assert rep.rules() == ["approval_promise", "tax_advice", "unreturned_rupee"]


# regression: live S03 answer (reports/20261010T211830Z_off) was a false positive
def test_tax_label_followed_by_non_advice_passes():
    text = ("**Tax savings:** The card's benefits don't include any tax savings. Its rewards and perks "
            "such as lounge access are not tax deductions. I can't estimate tax savings from this card.")
    assert check_tax_advice(text) == []


def test_tax_label_followed_by_advice_still_flagged():
    assert check_tax_advice("**Tax savings:** Pay your insurance on it to save tax under 80D.")


def test_negated_tax_claim_passes():
    assert check_tax_advice("Card rewards are not tax-free income in every case; I don't advise on that.") == []
