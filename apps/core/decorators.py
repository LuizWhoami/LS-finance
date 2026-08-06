"""
Decorators para rate limiting em views específicas.
"""

from django.core.cache import cache
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from functools import wraps


def rate_limit(requests=30, seconds=60, block_duration=3600):
    """
    Decorator para limitar requisições em views específicas.
    
    Uso:
        @rate_limit(requests=5, seconds=60)
        def minha_view(request):
            return HttpResponse('OK')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Obter IP do cliente
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            
            # Verificar se o IP está bloqueado
            block_key = f'blocked_view:{ip}'
            if cache.get(block_key, False):
                return HttpResponse(
                    '⚠️ Você foi bloqueado temporariamente. Tente novamente mais tarde.',
                    status=429
                )
            
            # Verificar limite
            cache_key = f'ratelimit_view:{ip}:{view_func.__name__}'
            count = cache.get(cache_key, 0)
            
            if count >= requests:
                # Bloquear IP
                cache.set(block_key, True, block_duration)
                return HttpResponse(
                    '⚠️ Muitas requisições. Você foi bloqueado temporariamente.',
                    status=429
                )
            
            # Incrementar contagem
            if count == 0:
                cache.set(cache_key, 1, seconds)
            else:
                cache.incr(cache_key)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def login_rate_limit():
    """Decorator específico para tentativas de login."""
    return rate_limit(requests=5, seconds=60, block_duration=1800)  # 5 tentativas/min, bloqueia 30min


def appointment_rate_limit():
    """Decorator específico para criação de agendamentos."""
    return rate_limit(requests=10, seconds=300, block_duration=3600)  # 10 agendamentos/5min, bloqueia 1h
