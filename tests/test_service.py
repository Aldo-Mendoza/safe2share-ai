from safe2share.service import Safe2ShareService


def test_service_local_mode():
    svc = Safe2ShareService(mode="local")
    r = svc.analyze("Public announcement: all users can read this.")
    assert r.risk in ("PUBLIC", "INTERNAL", "CONFIDENTIAL",
                      "HIGHLY CONFIDENTIAL")  # ensure valid


def test_service_auto_mode_falls_back():
    svc = Safe2ShareService(mode="auto")
    # No api key provided. AI model may fail; service should still return rule-based result
    r = svc.analyze("Contact: john.doe@example.com")
    assert r.score >= 60
