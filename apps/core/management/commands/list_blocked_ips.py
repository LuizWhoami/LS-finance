"""
Comando para listar todos os IPs bloqueados.
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Lista todos os IPs bloqueados'

    def handle(self, *args, **options):
        # Não temos uma forma fácil de listar todas as chaves no cache
        # Esta é uma implementação simples
        self.stdout.write(self.style.WARNING('Para listar IPs bloqueados, verifique os logs.'))
        self.stdout.write('Comando para desbloquear: python manage.py unblock_ip <IP>')
