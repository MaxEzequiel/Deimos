

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    
    // ================================================
    // CONVERTIR MENSAJES DE DJANGO A NOTIFICACIONES FLOTANTES
    // ================================================
    function convertDjangoMessages() {
        const messages = document.querySelectorAll('.alert');
        
        if (messages.length === 0) return;
        
        // contenedor flotante si no existe
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }
        
        messages.forEach(function(message) {
            // Ocultar el mensaje original
            message.style.display = 'none';
            
            // Determinar tipo
            let type = 'info';
            if (message.classList.contains('alert-success')) type = 'success';
            else if (message.classList.contains('alert-error')) type = 'error';
            else if (message.classList.contains('alert-danger')) type = 'error';
            else if (message.classList.contains('alert-warning')) type = 'warning';
            else if (message.classList.contains('alert-info')) type = 'info';
            
            // Duración según tipo
            let duration = 4000;
            if (type === 'success') duration = 3000;
            if (type === 'error') duration = 5000;
            if (type === 'warning') duration = 4000;
            
            //notificación flotante
            const toast = document.createElement('div');
            toast.className = `toast-notification toast-${type}`;
            toast.innerHTML = message.innerText || message.textContent;
            
            toastContainer.appendChild(toast);
            
            // Auto-desaparecer
            setTimeout(function() {
                toast.style.animation = 'fadeOutRight 0.3s ease-out';
                setTimeout(function() {
                    toast.remove();
                    if (toastContainer.children.length === 0) {
                        toastContainer.remove();
                    }
                }, 300);
            }, duration);
            
            // Cerrar al hacer clic
            toast.addEventListener('click', function() {
                toast.style.animation = 'fadeOutRight 0.2s ease-out';
                setTimeout(() => toast.remove(), 200);
            });
        });
    }
    
    // ================================================
    // VALIDACIÓN DE FORMULARIOS CON REQUIRED
    // ================================================
    function setupFormValidation() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(function(form) {
            // Desactivar validación nativa del navegador
            form.setAttribute('novalidate', true);
            
            form.addEventListener('submit', function(e) {
                const requiredFields = form.querySelectorAll('[required]');
                let hasError = false;
                
                for (const field of requiredFields) {
                    if (!field.value.trim()) {
                        hasError = true;
                        const fieldName = field.getAttribute('placeholder') || 
                                         field.getAttribute('name') || 
                                         'Este campo';
                        
                        // Mostrar notificación con Noty si está disponible
                        if (typeof Noty !== 'undefined') {
                            new Noty({
                                text: `${fieldName} es obligatorio`,
                                type: 'warning',
                                timeout: 3000,
                                layout: 'topRight'
                            }).show();
                        } else {
                            // Fallback si Noty no está cargado
                            alert(`${fieldName} es obligatorio`);
                        }
                        
                        field.focus();
                        e.preventDefault();
                        break;
                    }
                }
                
                if (hasError) {
                    e.preventDefault();
                }
            });
        });
    }
    
    // ================================================
    // FUNCIÓN PARA MOSTRAR NOTIFICACIONES MANUALES
    // ================================================
    window.showNotification = function(message, type = 'info', duration = 3000) {
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }
        
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.innerHTML = message;
        toastContainer.appendChild(toast);
        
        setTimeout(function() {
            toast.style.animation = 'fadeOutRight 0.3s ease-out';
            setTimeout(function() {
                toast.remove();
                if (toastContainer.children.length === 0) {
                    toastContainer.remove();
                }
            }, 300);
        }, duration);
        
        toast.addEventListener('click', function() {
            toast.style.animation = 'fadeOutRight 0.2s ease-out';
            setTimeout(() => toast.remove(), 200);
        });
    };
    
    // ================================================
    // EJECUTAR TODO
    // ================================================
    convertDjangoMessages();
    setupFormValidation();
});