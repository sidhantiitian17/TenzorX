"""
Custom exceptions for the TenzorX backend.
"""


class TenzorXError(Exception):
    """Base exception for all TenzorX errors."""
    pass


class NVIDIAAPIError(TenzorXError):
    """Raised when NVIDIA API call fails."""
    pass


class Neo4jError(TenzorXError):
    """Raised when Neo4j operation fails."""
    pass


class ICD10MappingError(TenzorXError):
    """Raised when ICD-10 code mapping fails."""
    pass


class CostEstimationError(TenzorXError):
    """Raised when cost estimation fails."""
    pass


class LoanEvaluationError(TenzorXError):
    """Raised when loan evaluation fails."""
    pass


class ValidationError(TenzorXError):
    """Raised when input validation fails."""
    pass
