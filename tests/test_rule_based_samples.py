import json
import pytest
import os
from safe2share.analyzers.rule_based import RuleBasedAnalyzer

# Path to the samples file, assuming the recommended structure: tests/fixtures/samples.json
SAMPLES_FILE = os.path.join(os.path.dirname(__file__), 'fixtures', 'samples.json')

# Load the test data once for all tests
@pytest.fixture(scope="module")
def sample_data():
    with open(SAMPLES_FILE, 'r') as f:
        return json.load(f)

# --- Test Function ---

def test_rule_based_analyzer_against_samples(sample_data):
    """
    Tests the RuleBasedAnalyzer against a variety of sample texts 
    to ensure keyword, PII, and scoring are correct.
    """
    analyzer = RuleBasedAnalyzer()
    
    # Run all samples
    for sample in sample_data:
        # Use analyze_with_info if you were testing the Service, 
        # but here we test the Analyzer directly:
        result = analyzer.analyze(sample['text'])

        if sample['id'] == 0:
            # ID 0: Public blog post
            assert result.risk == "PUBLIC"
            assert result.score == 0
            assert result.detections == []
            
        elif sample['id'] == 1:
            # ID 1: Internal use only, includes email and phone (PII)
            assert result.risk == "CONFIDENTIAL" # PII score is 70, which is CONFIDENTIAL
            assert result.score == 70
            assert "EMAIL" in [d.label for d in result.detections]
            assert "PHONE" in [d.label for d in result.detections]
            
        elif sample['id'] == 2:
            # ID 2: Contains "password", "Do not publish"
            assert result.risk == "HIGHLY_CONFIDENTIAL" # Keyword 'password' is 90
            assert result.score == 90
            assert any(d.span.lower() == 'password' for d in result.detections)
            
        elif sample['id'] == 3:
            # ID 3: Public content
            assert result.risk == "PUBLIC"
            assert result.score == 0
            assert result.detections == []

        else:
            pytest.fail(f"Sample ID {sample['id']} not handled in test logic.")