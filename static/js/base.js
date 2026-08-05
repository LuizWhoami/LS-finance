/**
 * Barbearia LS - JavaScript Base
 * Funções utilitárias e inicialização
 */

(function() {
    'use strict';

    // ==========================================================================
    // Document Ready
    // ==========================================================================
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Barbearia LS inicializada!');
        
        // Inicializar tooltips do Bootstrap
        initTooltips();
        
        // Inicializar popovers do Bootstrap
        initPopovers();
        
        // Configurar máscaras de formulário
        initFormMasks();
        
        // Configurar auto-dismiss de alerts
        initAlerts();
        
        // Configurar sidebar mobile
        initMobileSidebar();
    });

    // ==========================================================================
    // Funções de Inicialização
    // ==========================================================================

    /**
     * Inicializa tooltips do Bootstrap
     */
    function initTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    /**
     * Inicializa popovers do Bootstrap
     */
    function initPopovers() {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function(popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }

    /**
     * Configura máscaras para campos de formulário
     */
    function initFormMasks() {
        // Telefone (mask será adicionado via biblioteca no futuro)
        const phoneInputs = document.querySelectorAll('input[type="tel"]');
        phoneInputs.forEach(function(input) {
            input.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, '');
                if (value.length <= 11) {
                    if (value.length <= 2) {
                        value = value.replace(/^(\d{0,2})/, '($1');
                    } else if (value.length <= 6) {
                        value = value.replace(/^(\d{2})(\d{0,4})/, '($1) $2');
                    } else {
                        value = value.replace(/^(\d{2})(\d{5})(\d{0,4})/, '($1) $2-$3');
                    }
                    e.target.value = value;
                }
            });
        });

        // CPF
        const cpfInputs = document.querySelectorAll('input[data-mask="cpf"]');
        cpfInputs.forEach(function(input) {
            input.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, '');
                if (value.length <= 11) {
                    value = value.replace(/^(\d{3})(\d{0,3})(\d{0,3})(\d{0,2})/, function(match, p1, p2, p3, p4) {
                        let result = p1;
                        if (p2) result += '.' + p2;
                        if (p3) result += '.' + p3;
                        if (p4) result += '-' + p4;
                        return result;
                    });
                    e.target.value = value;
                }
            });
        });
    }

    /**
     * Auto-dismiss de alerts após 5 segundos
     */
    function initAlerts() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            setTimeout(function() {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        });
    }

    /**
     * Configura sidebar mobile com offcanvas
     */
    function initMobileSidebar() {
        const sidebarToggle = document.querySelector('[data-bs-toggle="offcanvas"][data-bs-target="#sidebarOffcanvas"]');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', function() {
                const offcanvas = document.querySelector('#sidebarOffcanvas');
                const bsOffcanvas = new bootstrap.Offcanvas(offcanvas);
                bsOffcanvas.show();
            });
        }
    }

    // ==========================================================================
    // Funções Utilitárias Globais
    // ==========================================================================

    /**
     * Formata valor para moeda brasileira (R$)
     */
    window.formatCurrency = function(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    };

    /**
     * Formata data para o padrão brasileiro
     */
    window.formatDate = function(dateString) {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('pt-BR').format(date);
    };

    /**
     * Formata data e hora
     */
    window.formatDateTime = function(dateString) {
        const date = new Date(dateString);
        return new Intl.DateTimeFormat('pt-BR', {
            dateStyle: 'short',
            timeStyle: 'short'
        }).format(date);
    };

    /**
     * Exibe loading em um elemento
     */
    window.showLoading = function(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Carregando...</span>
                    </div>
                    <p class="mt-2 text-muted">Carregando...</p>
                </div>
            `;
        }
    };

    /**
     * Confirmação de ação antes de executar
     */
    window.confirmAction = function(message, callback) {
        if (confirm(message || 'Tem certeza que deseja realizar esta ação?')) {
            callback();
        }
    };

    /**
     * Faz requisição AJAX com fetch
     */
    window.apiRequest = async function(url, options = {}) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                    ...options.headers
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    };

    /**
     * Obtém o token CSRF do cookie
     */
    function getCsrfToken() {
        const name = 'csrftoken';
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith(name + '='))
            ?.split('=')[1];
        return cookieValue || '';
    }

})();
