
### 🛠️ Instalação

1. Clone o repositório
2. Crie um ambiente virtual
3. Instale as dependências
4. Configure as variáveis de ambiente
5. Execute as migrações
6. Inicie o servidor

### 📚 Documentação
Consulte a pasta `docs/` para documentação detalhada.

### 📝 Licença
Este projeto é propriedade da Barbearia LS.
EOF
print_success "README.md criado com sucesso!"

# requirements.txt
print_message "Criando requirements.txt..."
cat > requirements.txt << 'EOF'
Django>=5.0,<6.0
django-environ>=0.11.2
psycopg2-binary>=2.9.9
Pillow>=10.0.0
django-crispy-forms>=2.1
crispy-bootstrap5>=0.7
django-import-export>=3.2
django-filter>=23.3
django-debug-toolbar>=4.0
python-dotenv>=1.0.0
celery>=5.3.0
redis>=5.0.0
django-celery-beat>=2.5.0
django-celery-results>=2.5.0
django-ckeditor>=6.7.0
django-extensions>=3.2.0
django-widget-tweaks>=1.4.0
whitenoise>=6.5.0
gunicorn>=21.2.0
EOF
print_success "requirements.txt criado com sucesso!"

# docker-compose.yml (futuro)
print_message "Criando docker-compose.yml..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_DB=barbearia_ls
      - POSTGRES_USER=barbearia_user
      - POSTGRES_PASSWORD=barbearia_password
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql://barbearia_user:barbearia_password@db:5432/barbearia_ls
      - REDIS_URL=redis://redis:6379/0

volumes:
  postgres_data:
EOF
print_success "docker-compose.yml criado com sucesso!"

# Dockerfile (futuro)
print_message "Criando Dockerfile..."
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
EOF
print_success "Dockerfile criado com sucesso!"

# manage.py (se não existir)
if [ ! -f "manage.py" ]; then
    print_message "Criando manage.py..."
    cat > manage.py << 'EOF'
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
EOF
    chmod +x manage.py
    print_success "manage.py criado com sucesso!"
else
    print_warning "manage.py já existe, mantendo o original."
fi

# =============================================================================
# 12. Estrutura de fixtures
# =============================================================================

print_section "12. Criando fixtures"

create_file "fixtures/users.json"
create_file "fixtures/services.json"
create_file "fixtures/professionals.json"
create_file "fixtures/initial_data.json"

print_success "Fixtures criadas com sucesso!"

# =============================================================================
# 13. Estrutura de internacionalização
# =============================================================================

print_section "13. Criando estrutura de internacionalização"

create_dir "locale/pt_BR"
create_dir "locale/pt_BR/LC_MESSAGES"

print_success "Estrutura de internacionalização criada com sucesso!"

# =============================================================================
# 14. Configuração de permissões
# =============================================================================

print_section "14. Configurando permissões"

# Tornar scripts executáveis
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x manage.py 2>/dev/null || true

# Criar arquivo .env a partir do .env.example (se não existir)
if [ ! -f ".env" ]; then
    print_message "Criando .env a partir do .env.example..."
    cp .env.example .env
    print_success ".env criado com sucesso!"
else
    print_warning ".env já existe, mantendo o original."
fi

print_success "Permissões configuradas com sucesso!"

# =============================================================================
# 15. Exibir árvore da estrutura criada
# =============================================================================

print_section "ESTRUTURA COMPLETA DO PROJETO"

if command -v tree &> /dev/null; then
    # Usar tree se disponível
    tree -L 3 -I '__pycache__|*.pyc|migrations' .
else
    print_warning "Tree não está instalado. Mostrando estrutura resumida:"
    echo ""
    echo "📁 barbearia_ls/"
    echo "  ├── 📁 apps/"
    echo "  │   ├── 📁 accounts/"
    echo "  │   ├── 📁 appointments/"
    echo "  │   ├── 📁 barbers/"
    echo "  │   ├── 📁 core/"
    echo "  │   ├── 📁 customers/"
    echo "  │   ├── 📁 finance/"
    echo "  │   ├── 📁 products/"
    echo "  │   ├── 📁 reports/"
    echo "  │   ├── 📁 services/"
    echo "  │   └── 📁 subscriptions/"
    echo "  ├── 📁 config/"
    echo "  │   ├── 📁 settings/"
    echo "  │   └── 📁 urls/"
    echo "  ├── 📁 docs/"
    echo "  ├── 📁 fixtures/"
    echo "  ├── 📁 logs/"
    echo "  ├── 📁 media/"
    echo "  │   ├── 📁 profiles/"
    echo "  │   ├── 📁 services/"
    echo "  │   └── 📁 temporary/"
    echo "  ├── 📁 scripts/"
    echo "  ├── 📁 static/"
    echo "  │   ├── 📁 css/"
    echo "  │   ├── 📁 fonts/"
    echo "  │   ├── 📁 icons/"
    echo "  │   ├── 📁 images/"
    echo "  │   ├── 📁 js/"
    echo "  │   └── 📁 vendor/"
    echo "  ├── 📁 templates/"
    echo "  │   ├── 📁 includes/"
    echo "  │   └── (templates dos apps)"
    echo "  ├── 📁 tests/"
    echo "  ├── 📄 .env.example"
    echo "  ├── 📄 .gitignore"
    echo "  ├── 📄 Dockerfile"
    echo "  ├── 📄 README.md"
    echo "  ├── 📄 docker-compose.yml"
    echo "  ├── 📄 manage.py"
    echo "  └── 📄 requirements.txt"
fi

# =============================================================================
# Resumo final
# =============================================================================

print_section "✅ PROJETO CONFIGURADO COM SUCESSO!"

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ${BOLD}Barbearia LS - Estrutura do Projeto${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}📦 ${BOLD}Apps criados:${NC} ${#APPS[@]} apps"
echo -e "   ${APPS[*]}"
echo ""
echo -e "${CYAN}📁 ${BOLD}Diretórios criados:${NC} $(find . -type d -not -path '*/\.*' | wc -l) diretórios"
echo -e "${CYAN}📄 ${BOLD}Arquivos criados:${NC} $(find . -type f -not -path '*/\.*' | wc -l) arquivos"
echo ""
echo -e "${YELLOW}⚠️  ${BOLD}Próximos passos:${NC}"
echo -e "   1. Configurar as variáveis no arquivo ${BOLD}.env${NC}"
echo -e "   2. Executar ${BOLD}python manage.py migrate${NC}"
echo -e "   3. Criar um superusuário: ${BOLD}python manage.py createsuperuser${NC}"
echo -e "   4. Iniciar o servidor: ${BOLD}python manage.py runserver${NC}"
echo ""
echo -e "${GREEN}${BOLD}✓ Projeto pronto para desenvolvimento!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# =============================================================================
# Fim do script
# =============================================================================

exit 0
