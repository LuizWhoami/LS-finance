"""
Validações comuns reutilizáveis em todo o sistema.
"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_cpf(value):
    """
    Valida CPF.
    """
    cpf = re.sub(r'[^0-9]', '', str(value))
    
    if len(cpf) != 11:
        raise ValidationError(_('CPF deve ter 11 dígitos.'))
    
    # Verifica se todos os dígitos são iguais
    if len(set(cpf)) == 1:
        raise ValidationError(_('CPF inválido.'))
    
    # Validação do primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    resto = 11 - (soma % 11)
    if resto >= 10:
        resto = 0
    if resto != int(cpf[9]):
        raise ValidationError(_('CPF inválido.'))
    
    # Validação do segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    resto = 11 - (soma % 11)
    if resto >= 10:
        resto = 0
    if resto != int(cpf[10]):
        raise ValidationError(_('CPF inválido.'))


def validate_phone(value):
    """
    Valida número de telefone.
    """
    phone = re.sub(r'[^0-9]', '', str(value))
    
    if len(phone) < 10 or len(phone) > 11:
        raise ValidationError(_('Telefone deve ter 10 ou 11 dígitos.'))
    
    if len(phone) == 11 and phone[2] not in '9876543210':
        raise ValidationError(_('Telefone inválido.'))


def validate_positive(value):
    """
    Valida se o valor é positivo.
    """
    if value <= 0:
        raise ValidationError(_('O valor deve ser positivo.'))


def validate_percentage(value):
    """
    Valida se o valor é uma porcentagem (0-100).
    """
    if value < 0 or value > 100:
        raise ValidationError(_('A porcentagem deve estar entre 0 e 100.'))


def validate_time_interval(start, end):
    """
    Valida se o horário de início é anterior ao horário de fim.
    """
    if start >= end:
        raise ValidationError(_('O horário de início deve ser anterior ao horário de fim.'))
