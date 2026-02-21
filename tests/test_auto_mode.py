from safe2share.analyzers.auto_combined import AutoCombinedAnalyzer, AutoPolicy
from safe2share.models import AnalysisResult


class FakeAnalyzer:
    def __init__(self, result: AnalysisResult, available: bool = True):
        self._result = result
        self._available = available

    @property
    def is_available(self) -> bool:
        return self._available

    def analyze(self, text: str) -> AnalysisResult:
        return self._result


def test_auto_does_not_escalate_on_public_without_hints():
    local = FakeAnalyzer(
        AnalysisResult(
            risk="PUBLIC",
            score=0,
            reasons=["No sensitive patterns found"],
            detections=[],
            suggested_rewrites=[],
            metadata={"analyzer": "fake_local"},
        )
    )
    llm = FakeAnalyzer(
        AnalysisResult(
            risk="HIGHLY_CONFIDENTIAL",
            score=100,
            reasons=["LLM says bad"],
            detections=[],
            suggested_rewrites=["[REDACTED]"],
            metadata={"analyzer": "fake_llm"},
        )
    )

    auto = AutoCombinedAnalyzer(local=local, llm=llm, policy=AutoPolicy())
    r = auto.analyze("hello world")

    assert r.risk == "PUBLIC"
    assert r.metadata["provider"] == "auto"
    assert r.metadata["auto_path"] == "local_only"
    assert r.metadata["auto_escalated"] == "false"
    # If you added this metadata field, keep this assertion:
    if "auto_hint_triggered" in r.metadata:
        assert r.metadata["auto_hint_triggered"] == "false"


def test_auto_escalates_on_public_when_hint_present_and_llm_available():
    """
    Even if local finds nothing, AUTO should escalate when the text contains
    a high-risk intent phrase (e.g., safe code / pin / otp).
    """
    local = FakeAnalyzer(
        AnalysisResult(
            risk="PUBLIC",
            score=0,
            reasons=["No sensitive patterns found"],
            detections=[],
            suggested_rewrites=[],
            metadata={"analyzer": "fake_local"},
        )
    )
    llm = FakeAnalyzer(
        AnalysisResult(
            risk="HIGHLY_CONFIDENTIAL",
            score=90,
            reasons=["Contains a safe/pin code value."],
            detections=[],
            suggested_rewrites=["[REDACTED]"],
            metadata={"model": "fake-model"},
        )
    )

    # Use a policy with a controlled hint list so the test is stable
    policy = AutoPolicy(escalate_hints=("code to my safe",))

    auto = AutoCombinedAnalyzer(local=local, llm=llm, policy=policy)
    r = auto.analyze("the code to my safe is 87362")

    assert r.metadata["provider"] == "auto"
    assert r.metadata["auto_escalated"] == "true"
    assert r.metadata["auto_path"] == "escalated_to_llm"
    assert r.metadata["auto_local_risk"] == "PUBLIC"
    assert r.metadata["auto_local_score"] == "0"
    if "auto_hint_triggered" in r.metadata:
        assert r.metadata["auto_hint_triggered"] == "true"
    assert r.risk == "HIGHLY_CONFIDENTIAL"


def test_auto_escalates_on_confidential_when_llm_available():
    local = FakeAnalyzer(
        AnalysisResult(
            risk="CONFIDENTIAL",
            score=70,
            reasons=["local detected secret-ish"],
            detections=[],
            suggested_rewrites=["local redact"],
            metadata={"analyzer": "fake_local"},
        )
    )
    llm = FakeAnalyzer(
        AnalysisResult(
            risk="HIGHLY_CONFIDENTIAL",
            score=95,
            reasons=["Contains a password value."],
            detections=[],
            suggested_rewrites=["My password is [REDACTED]."],
            metadata={"model": "fake-model"},
        )
    )

    auto = AutoCombinedAnalyzer(local=local, llm=llm, policy=AutoPolicy())
    r = auto.analyze("password blah")

    assert r.risk == "HIGHLY_CONFIDENTIAL"
    assert r.metadata["provider"] == "auto"
    assert r.metadata["auto_path"] == "escalated_to_llm"
    assert r.metadata["auto_escalated"] == "true"
    assert r.metadata["auto_local_risk"] == "CONFIDENTIAL"


def test_auto_falls_back_to_local_if_llm_unavailable_when_escalation_needed():
    local = FakeAnalyzer(
        AnalysisResult(
            risk="HIGHLY_CONFIDENTIAL",
            score=100,
            reasons=["local found key"],
            detections=[],
            suggested_rewrites=["[REDACTED]"],
            metadata={"analyzer": "fake_local"},
        )
    )
    llm = FakeAnalyzer(
        AnalysisResult(
            risk="PUBLIC",
            score=0,
            reasons=[],
            detections=[],
            suggested_rewrites=[],
            metadata={"analyzer": "fake_llm"},
        ),
        available=False,
    )

    auto = AutoCombinedAnalyzer(local=local, llm=llm, policy=AutoPolicy())
    r = auto.analyze("secret stuff")

    assert r.risk == "HIGHLY_CONFIDENTIAL"
    assert r.metadata["provider"] == "auto"
    assert r.metadata["auto_path"] == "local_only_llm_unavailable"
    assert r.metadata["auto_escalated"] == "true"
