"""
Middlewares de segurança customizados.
"""

from django.http import HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.conf import settings
import re
from datetime import datetime, timedelta


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Adiciona cabeçalhos de segurança adicionais."""
    
    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        return response


class BlockSuspiciousRequestsMiddleware(MiddlewareMixin):
    """Bloqueia requests suspeitos."""
    
    def process_request(self, request):
        # Bloquear tentativas de SQL Injection
        sql_patterns = [
            r'(?i)(union|select|insert|delete|update|drop|alter|create|truncate)',
            r'(?i)(--|\|\||&&)',
            r'(?i)(;|\b(?:or|and)\b)',
        ]
        
        query_string = request.META.get('QUERY_STRING', '')
        for pattern in sql_patterns:
            if re.search(pattern, query_string):
                return HttpResponse('Solicitação bloqueada por razões de segurança.', status=403)
        
        # Bloquear path traversal
        if '..' in request.path:
            return HttpResponse('Solicitação bloqueada por razões de segurança.', status=403)
        
        return None


class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware de rate limiting por IP.
    Bloqueia IPs que fazem muitas requisições em um curto período.
    """
    
    # Configurações por URL
    RATE_LIMITS = {
        'default': {'requests': 60, 'seconds': 300},  # 60 requisições em 5 minutos
        'login': {'requests': 10, 'seconds': 60},     # 10 tentativas de login por minuto
        'register': {'requests': 5, 'seconds': 300},  # 5 cadastros por 5 minutos
        'appointment': {'requests': 20, 'seconds': 300}, # 20 agendamentos por 5 minutos
        'admin': {'requests': 30, 'seconds': 60},    # 30 requisições ao admin por minuto
        'api': {'requests': 100, 'seconds': 60},     # 100 requisições à API por minuto
        'static': {'requests': 200, 'seconds': 60},  # 200 requisições a arquivos estáticos por minuto
    }
    
    # Tempo de bloqueio para IPs que excederam o limite
    BLOCK_DURATION = 3600  # 1 hora bloqueado
    
    def process_request(self, request):
        # Obter IP do cliente
        ip = self.get_client_ip(request)
        
        # Verificar se o IP está bloqueado
        if self.is_ip_blocked(ip):
            return HttpResponse(
                '⚠️ IP bloqueado temporariamente devido a muitas requisições. Tente novamente mais tarde.',
                status=429  # Too Many Requests
            )
        
        # Determinar o tipo de requisição
        rate_type = self.get_rate_type(request)
        limit = self.RATE_LIMITS.get(rate_type, self.RATE_LIMITS['default'])
        
        # Verificar limite
        if not self.check_rate_limit(ip, rate_type, limit):
            self.block_ip(ip)
            return HttpResponse(
                '⚠️ Muitas requisições. Você foi bloqueado temporariamente.',
                status=429
            )
        
        return None
    
    def get_client_ip(self, request):
        """Obtém o IP real do cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_rate_type(self, request):
        """Determina o tipo de requisição para aplicar o rate limit adequado."""
        path = request.path
        
        if '/auth/login/' in path or '/login/' in path:
            return 'login'
        elif '/register/' in path or '/cadastro/' in path:
            return 'register'
        elif '/appointment/' in path or '/agendar/' in path:
            return 'appointment'
        elif '/admin/' in path or '/dashboard/' in path:
            return 'admin'
        elif '/api/' in path:
            return 'api'
        elif '/static/' in path or '/media/' in path:
            return 'static'
        else:
            return 'default'
    
    def check_rate_limit(self, ip, rate_type, limit):
        """Verifica se o IP excedeu o limite de requisições."""
        cache_key = f'ratelimit:{rate_type}:{ip}'
        
        # Obter contagem atual
        count = cache.get(cache_key, 0)
        
        if count >= limit['requests']:
            return False
        
        # Incrementar contagem
        if count == 0:
            # Primeira requisição, definir expiração
            cache.set(cache_key, 1, limit['seconds'])
        else:
            # Incrementar contagem existente
            cache.incr(cache_key)
        
        return True
    
    def block_ip(self, ip):
        """Bloqueia um IP por um período determinado."""
        block_key = f'blocked_ip:{ip}'
        cache.set(block_key, True, self.BLOCK_DURATION)
        
        # Registrar no log
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f'IP {ip} bloqueado por excesso de requisições.')
    
    def is_ip_blocked(self, ip):
        """Verifica se o IP está bloqueado."""
        block_key = f'blocked_ip:{ip}'
        return cache.get(block_key, False)
