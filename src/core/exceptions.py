"""Custom exception hierarchy for PixelPilot.

Provides structured error handling with specific exception types
for different failure modes across the application.
"""


class PixelPilotError(Exception):
    """
    Base exception for all PixelPilot errors.
    
    All custom exceptions should inherit from this class to allow
    catching all application-specific errors.
    """
    pass


# ==================== Vision System Errors ====================

class VisionError(PixelPilotError):
    """Base exception for vision system errors."""
    pass


class VisionStrategyError(VisionError):
    """Raised when no suitable vision strategy is available."""
    pass


class ScreenCaptureError(VisionError):
    """Raised when screen capture fails."""
    pass


class ColorMatchError(VisionError):
    """Raised when color matching operation fails."""
    pass


# ==================== Input System Errors ====================

class InputError(PixelPilotError):
    """Base exception for input system errors."""
    pass


class InputStrategyError(InputError):
    """Raised when no suitable input strategy is available."""
    pass


class KeyPressError(InputError):
    """Raised when key press simulation fails."""
    pass


class MouseControlError(InputError):
    """Raised when mouse control operation fails."""
    pass


class PermissionError(InputError):
    """Raised when insufficient permissions for input operations."""
    pass


# ==================== Graph System Errors ====================

class GraphError(PixelPilotError):
    """Base exception for graph-related errors."""
    pass


class CyclicGraphError(GraphError):
    """Raised when a graph contains cycles (not allowed in FBD)."""
    pass


class InvalidNodeError(GraphError):
    """Raised when a node is invalid or misconfigured."""
    pass


class InvalidLinkError(GraphError):
    """Raised when attempting to create an invalid link."""
    pass


class GraphTooLargeError(GraphError):
    """Raised when graph exceeds maximum node count."""
    pass


class ExecutionError(GraphError):
    """Raised when graph execution fails."""
    pass


# ==================== Serialization Errors ====================

class SerializationError(PixelPilotError):
    """Base exception for serialization errors."""
    pass


class DeserializationError(SerializationError):
    """Raised when deserialization fails."""
    pass


class InvalidFileFormatError(SerializationError):
    """Raised when file format is invalid or unsupported."""
    pass


class VersionMismatchError(SerializationError):
    """Raised when file version is incompatible."""
    pass


# ==================== Configuration Errors ====================

class ConfigurationError(PixelPilotError):
    """Base exception for configuration errors."""
    pass


class InvalidConfigError(ConfigurationError):
    """Raised when configuration is invalid."""
    pass


class ConfigFileNotFoundError(ConfigurationError):
    """Raised when configuration file cannot be found."""
    pass


# ==================== Validation Errors ====================

class ValidationError(PixelPilotError):
    """Base exception for validation errors."""
    pass


class InvalidCoordinateError(ValidationError):
    """Raised when coordinates are invalid."""
    pass


class InvalidColorError(ValidationError):
    """Raised when color values are invalid."""
    pass


class InvalidKeyCodeError(ValidationError):
    """Raised when key code is invalid."""
    pass


# ==================== Engine Errors ====================

class EngineError(PixelPilotError):
    """Base exception for automation engine errors."""
    pass


class EngineStartError(EngineError):
    """Raised when engine fails to start."""
    pass


class EngineStopError(EngineError):
    """Raised when engine fails to stop cleanly."""
    pass


class RuleExecutionError(EngineError):
    """Raised when rule execution fails."""
    pass
