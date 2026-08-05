"""
Exceções customizadas do sistema.
"""


class BarbeariaException(Exception):
    """Exceção base do sistema."""
    pass


class BusinessRuleViolation(BarbeariaException):
    """Exceção lançada quando uma regra de negócio é violada."""
    pass


class AppointmentConflictError(BarbeariaException):
    """Exceção lançada quando há conflito de horários."""
    pass


class InvalidStatusTransition(BarbeariaException):
    """Exceção lançada quando uma transição de status é inválida."""
    pass


class ResourceNotFoundError(BarbeariaException):
    """Exceção lançada quando um recurso não é encontrado."""
    pass


class InsufficientStockError(BarbeariaException):
    """Exceção lançada quando não há estoque suficiente."""
    pass


class PaymentError(BarbeariaException):
    """Exceção lançada quando ocorre um erro no pagamento."""
    pass


class PermissionDeniedError(BarbeariaException):
    """Exceção lançada quando o usuário não tem permissão."""
    pass
