from safe2share.analyzers.rule_based import RuleBasedAnalyzer


def analyze(text: str):
    return RuleBasedAnalyzer().analyze(text)


def labels(result):
    return {d.label for d in (result.detections or [])}


def test_safe_text_is_public():
    r = analyze("Hello team, meeting at 3pm. Please review the agenda.")
    assert r.risk == "PUBLIC"
    assert r.score == 0
    assert r.detections == []
    assert "No sensitive patterns found" in " ".join(r.reasons)


def test_detects_password_assignment():
    r = analyze("My password is hunter42")
    assert r.risk in ("CONFIDENTIAL", "HIGHLY_CONFIDENTIAL")
    assert r.score >= 85
    assert "CREDENTIAL" in labels(r)
    assert any("[REDACTED]" in s for s in r.suggested_rewrites)


def test_detects_generic_token_secret():
    r = analyze("secret token: abc123")
    assert r.risk in ("CONFIDENTIAL", "HIGHLY_CONFIDENTIAL")
    assert r.score >= 80
    assert "SECRET" in labels(r)
    assert "[REDACTED]" in (r.suggested_rewrites[0]
                            if r.suggested_rewrites else "")


def test_detects_openai_style_api_key():
    r = analyze("Do not share this key: sk-abcdefghijklmnopqrstuvwxyz1234567890")
    assert r.risk == "HIGHLY_CONFIDENTIAL"
    assert r.score >= 90
    assert "API_KEY" in labels(r)


def test_detects_private_key_block_header():
    r = analyze("-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----")
    assert r.risk == "HIGHLY_CONFIDENTIAL"
    assert r.score == 100  # your detector sets 100 base
    assert "PRIVATE_KEY" in labels(r)


def test_detects_jwt_token_shape():
    # Minimal valid JWT-like structure for regex (header.payload.signature)
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." \
          "eyJ1c2VySWQiOiIxMjMiLCJyb2xlIjoiYWRtaW4ifQ." \
          "sflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    r = analyze(f"My JWT is {jwt}")
    assert r.risk == "HIGHLY_CONFIDENTIAL"
    assert r.score >= 90
    assert "JWT" in labels(r)


def test_detects_email_is_not_highly_confidential_by_default():
    r = analyze("Contact me at alice@example.com for details.")
    assert "EMAIL" in labels(r)
    # Email alone should not be 100; keep it moderate
    assert 20 <= r.score <= 80
    assert r.risk in ("INTERNAL", "CONFIDENTIAL", "HIGHLY_CONFIDENTIAL")


def test_detects_phone_is_reasonable():
    r = analyze("Call me at +1 (613) 555-1212 tomorrow.")
    assert "PHONE" in labels(r)
    assert 20 <= r.score <= 80


def test_multiple_detections_stack_score_upwards():
    r = analyze("My password is hunter42. Email me at alice@example.com.")
    assert "CREDENTIAL" in labels(r)
    assert "EMAIL" in labels(r)
    # Should be at least as severe as the credential baseline
    assert r.score >= 85
    assert r.risk in ("CONFIDENTIAL", "HIGHLY_CONFIDENTIAL")


def test_rewrite_redacts_detected_spans():
    text = "token: abc123 and password: hunter42"
    r = analyze(text)
    assert r.suggested_rewrites, "expected a rewrite suggestion"
    rewritten = r.suggested_rewrites[0]
    assert "[REDACTED]" in rewritten
    # should not contain the original secret spans
    assert "abc123" not in rewritten
    assert "hunter42" not in rewritten


def test_rewrite_redacts_only_value_for_password_assignment():
    r = analyze("My password is Mac&Cheese4")
    assert r.risk in ("CONFIDENTIAL", "HIGHLY_CONFIDENTIAL")
    assert any(d.label == "CREDENTIAL" for d in r.detections)
    assert r.suggested_rewrites
    assert "My password is [REDACTED]" in r.suggested_rewrites[0]


def test_high_entropy_without_context_does_not_trigger():
    # Looks like base64-ish, but no hint words like token/secret/key nearby.
    text = "Here is an example blob: QWxkb0FtZW5kb3NhZmUyU2hhcmVQcm9qZWN0VGVzdA=="
    r = analyze(text)
    # Should stay public (or at least not produce HIGH_ENTROPY)
    assert "HIGH_ENTROPY" not in labels(r)
    assert r.risk == "PUBLIC"
    assert r.score == 0


def test_high_entropy_with_context_triggers():
    text = "token: QWxkb0FtZW5kb3NhZmUyU2hhcmVQcm9qZWN0VGVzdA=="
    r = analyze(text)
    # In this case SECRET should trigger (token: ...)
    assert r.risk in ("CONFIDENTIAL", "HIGHLY_CONFIDENTIAL")
    assert ("SECRET" in labels(r)) or ("HIGH_ENTROPY" in labels(r))
