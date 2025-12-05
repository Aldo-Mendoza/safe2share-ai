# Analyzer Strategy interface

from abc import ABC, abstractmethod
from ..models import AnalysisResult


class BaseAnalyzer(ABC):
    """
    The abstract Strategy interface for all analysis modes.
    Every concrete analyzer must implement the analyze method.
    """

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """
        Checks if the analyzer is configured and ready to run 
        (e.g., checks for required API keys, hosts, etc.).
        """
        raise NotImplementedError

    @abstractmethod
    def analyze(self, text: str) -> AnalysisResult:
        """
        Analyzes the input text for sensitive information. If is_available is False, this method  raises a descriptive RuntimeError or return a null result.
        
        Args:
            text: The user-provided text to scan.
            
        Returns:
            An AnalysisResult model containing risk, score, and reasons.
        """
        raise NotImplementedError
