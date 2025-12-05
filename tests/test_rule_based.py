from safe2share.analyzers.rule_based import RuleBasedAnalyzer

# Base Case 1:
def test_rule_detects_email():
    text = "Contact me at alice@example.com for details."
    r = RuleBasedAnalyzer().analyze(text)
    assert r.score >= 60
    assert any(d.label == "EMAIL" for d in r.detections or [])
    assert "Detected email pattern" in " ".join(r.reasons) or any(
        "email" in rr.lower() for rr in r.reasons)

# Base Case 2:
def test_rule_detects_password_keyword():
    text = "My password is hunter42"
    r = RuleBasedAnalyzer().analyze(text)
    assert r.score >= 85 or r.risk in ("CONFIDENTIAL", "HIGHLY_CONFIDENTIAL")


def test_no_detection_is_public_risk():
    """Verifies that text with no detections is scored 0 and marked PUBLIC."""
    text = "This is a completely safe sentence about the weather."
    r = RuleBasedAnalyzer().analyze(text)
    assert r.score == 0
    assert r.risk == "PUBLIC"
    assert r.detections == []
    assert r.reasons == ["No sensitive patterns found"]


def test_internal_keyword_sets_base_score():
    """Verifies a low-risk keyword sets the score floor (25)."""
    text = "This document is strictly proprietary and internal."
    r = RuleBasedAnalyzer().analyze(text)
    assert r.score == 25
    assert r.risk == "INTERNAL"
    assert any(d.label == "INTERNAL" for d in r.detections)


def test_high_entropy_heuristic_score():
    """Verifies the potential secret heuristic is detected and scored 85."""
    # Base64-like string: A 32-character high-entropy string
    text = "The new JWT token is: Y29tcGxldGVzYWZlc2VudGVuY2V7d2VhdGhlcn0="
    r = RuleBasedAnalyzer().analyze(text)
    assert r.score == 85
    assert r.risk == "HIGHLY_CONFIDENTIAL"
    assert any(d.label == "POTENTIAL_SECRET" for d in r.detections)


# --- AGGREGATION AND COMPOUND RISK TESTS ---

def test_simple_pii_aggregation():
    """Verifies a single PII item uses max score + weight."""
    text = "Contact me at alice@example.com."
    r = RuleBasedAnalyzer().analyze(text)
    
    # Expected Score: 60 (base PII) + 2 (email weight) = 62
    assert r.score == 62
    assert r.risk == "CONFIDENTIAL"
    assert any(d.label == "EMAIL" for d in r.detections)


def test_quantity_wins_aggregation():
    """Verifies multiple identical PII items aggregate the score."""
    # 10 emails: Max score (60) + (10 * 2) weight = 80
    text = "e1@a.com, e2@b.com, e3@c.com, e4@d.com, e5@e.com, e6@f.com, e7@g.com, e8@h.com, e9@i.com, e10@j.com"
    r = RuleBasedAnalyzer().analyze(text)

    # Expected Score: 80
    assert r.score == 80
    assert "Score increased by 20 due to multiple PII/sensitive items." in r.reasons[0]
    assert len([d for d in r.detections if d.label == "EMAIL"]) == 10


def test_credit_card_escalation_to_max():
    """Verifies multiple high-weight PII items quickly hit the 100 cap."""
    # 3 Credit Cards: Max score (60) + (3 * 15) weight = 105. Capped at 100.
    text = "Card 1: 1234567812345678, Card 2: 9876543298765432, Card 3: 1111222233334444."
    r = RuleBasedAnalyzer().analyze(text)

    # Expected Score: 100 (Capped)
    assert r.score == 100
    assert r.risk == "HIGHLY_CONFIDENTIAL"
    assert len([d for d in r.detections if d.label == "CREDIT_CARD"]) == 3


def test_quality_dominates_aggregation():
    """Verifies that the highest single score (90) is always preserved, even when aggregated."""
    text = "The password is Pwd1. Call me at +1 555-1212. My email is a@b.com. Another email c@d.com."
    r = RuleBasedAnalyzer().analyze(text)

    # Expected Score: 90 (password) + 4 (2 emails) + 3 (1 phone) = 97
    assert r.score == 97 
    assert r.risk == "HIGHLY_CONFIDENTIAL"
    assert any(d.label == "HIGHLY_CONFIDENTIAL" for d in r.detections)
    
    assert "Score increased by 7 due to multiple PII/sensitive items." in r.reasons[0]