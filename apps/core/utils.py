"""
Utilitários gerais do sistema.
"""

import re
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.text import slugify


def generate_unique_slug(model, title, slug_field='slug', max_length=200):
    """
    Gera um slug único para o modelo.
    """
    base_slug = slugify(title)[:max_length]
    slug = base_slug
    counter = 1
    
    while model.objects.filter(**{slug_field: slug}).exists():
        suffix = f'-{counter}'
        slug = f'{base_slug[:max_length - len(suffix)]}{suffix}'
        counter += 1
    
    return slug


def format_currency(value):
    """
    Formata valor para moeda brasileira.
    """
    return f'R$ {value:,.2f}'.replace(',', 'v').replace('.', ',').replace('v', '.')


def format_phone(value):
    """
    Formata número de telefone.
    """
    phone = re.sub(r'[^0-9]', '', str(value))
    
    if len(phone) == 11:
        return f'({phone[:2]}) {phone[2:7]}-{phone[7:]}'
    elif len(phone) == 10:
        return f'({phone[:2]}) {phone[2:6]}-{phone[6:]}'
    return phone


def format_cpf(value):
    """
    Formata CPF.
    """
    cpf = re.sub(r'[^0-9]', '', str(value))
    if len(cpf) == 11:
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
    return cpf


def get_date_range(start_date, end_date):
    """
    Retorna uma lista de datas entre start_date e end_date.
    """
    delta = end_date - start_date
    return [start_date + timedelta(days=i) for i in range(delta.days + 1)]


def calculate_age(birth_date):
    """
    Calcula a idade a partir da data de nascimento.
    """
    today = timezone.now().date()
    age = today.year - birth_date.year
    
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    
    return age


def is_valid_uuid(value):
    """
    Verifica se o valor é um UUID válido.
    """
    import uuid
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


def truncate_text(text, max_length=100, suffix='...'):
    """
    Trunca um texto para um tamanho máximo.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length].strip() + suffix
