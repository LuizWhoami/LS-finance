/**
 * Barbearia LS - JavaScript do Cliente
 */

(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        console.log('Barbearia LS - Área do Cliente carregada!');
        
        initTooltips();
        initDatePickers();
        initPhoneMask();
    });

    function initTooltips() {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(el) {
            return new bootstrap.Tooltip(el);
        });
    }

    function initDatePickers() {
        var dateInputs = document.querySelectorAll('input[type="datetime-local"]');
        dateInputs.forEach(function(input) {
            if (!input.value) {
                var now = new Date();
                now.setHours(now.getHours() + 1);
                var formatted = now.toISOString().slice(0, 16);
                input.value = formatted;
            }
        });
    }

    function initPhoneMask() {
        var phoneInputs = document.querySelectorAll('input[name="phone"]');
        phoneInputs.forEach(function(input) {
            input.addEventListener('input', function(e) {
                var value = e.target.value.replace(/\D/g, '');
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
    }

    // Função para confirmar cancelamento
    window.confirmCancel = function(message) {
        return confirm(message || 'Tem certeza que deseja cancelar este agendamento?');
    };

})();
