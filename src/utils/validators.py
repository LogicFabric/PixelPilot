"""Input validation utilities for PixelPilot.

Provides validation functions for user inputs to ensure data integrity
and provide helpful error messages.
"""

from typing import Tuple, Optional


class ValidationError(ValueError):
    """Raised when input validation fails."""
    pass


def validate_coordinates(
    x: int,
    y: int,
    max_x: int = 9999,
    max_y: int = 9999,
    min_x: int = 0,
    min_y: int = 0
) -> Tuple[int, int]:
    """
    Validate and clamp screen coordinates.
    
    Args:
        x: X coordinate
        y: Y coordinate
        max_x: Maximum allowed X value
        max_y: Maximum allowed Y value
        min_x: Minimum allowed X value
        min_y: Minimum allowed Y value
        
    Returns:
        Tuple of validated (x, y) coordinates
        
    Raises:
        ValidationError: If coordinates are not integers or out of bounds
        
    Example:
        >>> x, y = validate_coordinates(100, 200)
        >>> x, y = validate_coordinates(-10, 5000, max_x=1920, max_y=1080)
    """
    try:
        x = int(x)
        y = int(y)
    except (TypeError, ValueError):
        raise ValidationError(f"Coordinates must be integers, got x={x}, y={y}")
    
    if x < min_x or x > max_x:
        raise ValidationError(f"X coordinate {x} out of bounds [{min_x}, {max_x}]")
    if y < min_y or y > max_y:
        raise ValidationError(f"Y coordinate {y} out of bounds [{min_y}, {max_y}]")
    
    return x, y


def validate_rgb(
    r: int,
    g: int,
    b: int,
    allow_alpha: bool = False
) -> Tuple[int, int, int]:
    """
    Validate RGB color values.
    
    Args:
        r: Red component (0-255)
        g: Green component (0-255)
        b: Blue component (0-255)
        allow_alpha: Whether to allow alpha channel (not yet implemented)
        
    Returns:
        Tuple of validated (r, g, b) values
        
    Raises:
        ValidationError: If color values are invalid
        
    Example:
        >>> r, g, b = validate_rgb(255, 128, 0)
        >>> r, g, b = validate_rgb(300, -10, 50)  # Raises ValidationError
    """
    try:
        r = int(r)
        g = int(g)
        b = int(b)
    except (TypeError, ValueError):
        raise ValidationError(f"RGB values must be integers, got r={r}, g={g}, b={b}")
    
    if not (0 <= r <= 255):
        raise ValidationError(f"Red value {r} must be in range [0, 255]")
    if not (0 <= g <= 255):
        raise ValidationError(f"Green value {g} must be in range [0, 255]")
    if not (0 <= b <= 255):
        raise ValidationError(f"Blue value {b} must be in range [0, 255]")
    
    return r, g, b


def validate_region(
    x: int,
    y: int,
    width: int,
    height: int,
    max_width: int = 9999,
    max_height: int = 9999
) -> Tuple[int, int, int, int]:
    """
    Validate screen region parameters.
    
    Args:
        x: Region X coordinate
        y: Region Y coordinate
        width: Region width
        height: Region height
        max_width: Maximum screen width
        max_height: Maximum screen height
        
    Returns:
        Tuple of validated (x, y, width, height)
        
    Raises:
        ValidationError: If region parameters are invalid
        
    Example:
        >>> region = validate_region(100, 100, 200, 150)
        >>> region = validate_region(0, 0, 1920, 1080, max_width=1920, max_height=1080)
    """
    x, y = validate_coordinates(x, y, max_x=max_width, max_y=max_height)
    
    try:
        width = int(width)
        height = int(height)
    except (TypeError, ValueError):
        raise ValidationError(f"Width and height must be integers, got {width}, {height}")
    
    if width <= 0:
        raise ValidationError(f"Width must be positive, got {width}")
    if height <= 0:
        raise ValidationError(f"Height must be positive, got {height}")
    
    if x + width > max_width:
        raise ValidationError(f"Region extends beyond screen width: {x}+{width} > {max_width}")
    if y + height > max_height:
        raise ValidationError(f"Region extends beyond screen height: {y}+{height} > {max_height}")
    
    return x, y, width, height


def validate_key_code(key_code: str) -> str:
    """
    Validate keyboard key code.
    
    Args:
        key_code: Key code string
        
    Returns:
        Validated lowercase key code
        
    Raises:
        ValidationError: If key code is invalid
        
    Example:
        >>> key = validate_key_code("space")
        >>> key = validate_key_code("A")  # Returns "a"
        >>> key = validate_key_code("")   # Raises ValidationError
    """
    if not isinstance(key_code, str):
        raise ValidationError(f"Key code must be a string, got {type(key_code)}")
    
    key_code = key_code.strip().lower()
    
    if not key_code:
        raise ValidationError("Key code cannot be empty")
    
    # Basic validation - could be extended with allowed key list
    if len(key_code) > 20:
        raise ValidationError(f"Key code too long: {key_code}")
    
    return key_code


def validate_tolerance(tolerance: int, min_val: int = 0, max_val: int = 255) -> int:
    """
    Validate color tolerance value.
    
    Args:
        tolerance: Tolerance value
        min_val: Minimum allowed tolerance
        max_val: Maximum allowed tolerance
        
    Returns:
        Validated tolerance value
        
    Raises:
        ValidationError: If tolerance is invalid
        
    Example:
        >>> tol = validate_tolerance(10)
        >>> tol = validate_tolerance(300)  # Raises ValidationError
    """
    try:
        tolerance = int(tolerance)
    except (TypeError, ValueError):
        raise ValidationError(f"Tolerance must be an integer, got {tolerance}")
    
    if not (min_val <= tolerance <= max_val):
        raise ValidationError(f"Tolerance {tolerance} must be in range [{min_val}, {max_val}]")
    
    return tolerance


def clamp(value: int, min_val: int, max_val: int) -> int:
    """
    Clamp a value within a range.
    
    Args:
        value: Value to clamp
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Clamped value
        
    Example:
        >>> clamp(150, 0, 100)  # Returns 100
        >>> clamp(-10, 0, 100)  # Returns 0
        >>> clamp(50, 0, 100)   # Returns 50
    """
    return max(min_val, min(value, max_val))
