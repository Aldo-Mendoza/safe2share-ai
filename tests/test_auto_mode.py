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


def test_auto_does_not_escalate_on_public():
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
    r = auto.analyze("hello")

    assert r.risk == "PUBLIC"
    assert r.metadata["provider"] == "auto"
    assert r.metadata["auto_path"] == "local_only"
    assert r.metadata["auto_escalated"] == "false"


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


def test_auto_falls_back_to_local_if_llm_unavailable():
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
