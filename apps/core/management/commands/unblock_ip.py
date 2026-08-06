"""
Comando para desbloquear um IP manualmente.
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Desbloqueia um IP que foi bloqueado pelo rate limit'

    def add_arguments(self, parser):
        parser.add_argument('ip', type=str, help='IP a ser desbloqueado')

    def handle(self, *args, **options):
        ip = options['ip']
        block_key = f'blocked_ip:{ip}'
        
        if cache.get(block_key, False):
            cache.delete(block_key)
            self.stdout.write(self.style.SUCCESS(f'IP {ip} desbloqueado com sucesso!'))
        else:
            self.stdout.write(self.style.WARNING(f'IP {ip} não está bloqueado.'))
