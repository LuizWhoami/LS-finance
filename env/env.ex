# Django Settings
SECRET_KEY=django-insecure-key-for-development
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.3,0.0.0.0

# Database
DB_NAME=barbearia_ls
DB_USER=barbearia_user
DB_PASSWORD=barbearia_password
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-password
EMAIL_USE_TLS=True

# Security
SECURE_SSL_REDIRECT=False
CSRF_TRUSTED_ORIGINS=http://localhost:8000

# Redis (para cache e celery)
REDIS_URL=redis://localhost:6379/1
