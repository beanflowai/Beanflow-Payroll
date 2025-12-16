"""Custom Exception Hierarchy for BeanFlow Payroll"""


class PayrollError(Exception):
    """Base exception for all payroll-related errors"""

    def __init__(self, message: str, details: str | None = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class AuthenticationError(PayrollError):
    """Authentication failed - invalid or missing credentials"""

    pass


class AuthorizationError(PayrollError):
    """Authorization failed - user lacks required permissions"""

    pass


class ValidationError(PayrollError):
    """Data validation failed"""

    pass


class NotFoundError(PayrollError):
    """Requested resource not found"""

    pass


class ConfigurationError(PayrollError):
    """Configuration error - missing or invalid settings"""

    pass


class DatabaseError(PayrollError):
    """Database operation failed"""

    pass
