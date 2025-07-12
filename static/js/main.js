// ReWear - Main JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Image preview functionality for upload forms
    const imageInput = document.querySelector('input[type="file"][accept*="image"]');
    if (imageInput) {
        imageInput.addEventListener('change', handleImagePreview);
    }

    // Form validation enhancements
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', handleFormValidation);
    });

    // Search form auto-submit on filter change
    const searchForm = document.querySelector('form[method="GET"]');
    if (searchForm && window.location.pathname.includes('/browse')) {
        const filterInputs = searchForm.querySelectorAll('select, input[type="number"]');
        filterInputs.forEach(input => {
            input.addEventListener('change', debounce(handleFilterChange, 500));
        });
    }

    // Notification auto-dismiss
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.querySelector('.btn-close')) {
                alert.querySelector('.btn-close').click();
            }
        }, 5000);
    });

    // Coin balance animation
    animateCoinBalance();

    // Item card hover effects
    enhanceItemCards();

    // Admin approval form enhancements
    enhanceAdminForms();

    // Navigation enhancements
    enhanceNavigation();
});

/**
 * Handle image preview for upload forms
 */
function handleImagePreview(event) {
    const files = event.target.files;
    const previewContainer = document.querySelector('.image-preview-container') || createPreviewContainer();
    
    previewContainer.innerHTML = '';
    
    if (files.length > 0) {
        Array.from(files).forEach((file, index) => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = createImagePreview(e.target.result, file.name, index);
                    previewContainer.appendChild(preview);
                };
                reader.readAsDataURL(file);
            }
        });
    }
}

/**
 * Create preview container for images
 */
function createPreviewContainer() {
    const container = document.createElement('div');
    container.className = 'image-preview-container row g-2 mt-2';
    
    const fileInput = document.querySelector('input[type="file"][accept*="image"]');
    if (fileInput) {
        fileInput.parentNode.appendChild(container);
    }
    
    return container;
}

/**
 * Create individual image preview
 */
function createImagePreview(src, filename, index) {
    const col = document.createElement('div');
    col.className = 'col-md-3 col-sm-4 col-6';
    
    col.innerHTML = `
        <div class="card">
            <img src="${src}" class="card-img-top" style="height: 100px; object-fit: cover;" alt="Preview ${index + 1}">
            <div class="card-body p-2">
                <small class="text-muted text-truncate d-block">${filename}</small>
            </div>
        </div>
    `;
    
    return col;
}

/**
 * Enhanced form validation
 */
function handleFormValidation(event) {
    const form = event.target;
    
    if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
        
        // Focus on first invalid field
        const firstInvalid = form.querySelector(':invalid');
        if (firstInvalid) {
            firstInvalid.focus();
        }
    }
    
    form.classList.add('was-validated');
}

/**
 * Handle filter changes in search/browse forms
 */
function handleFilterChange(event) {
    const form = event.target.closest('form');
    if (form) {
        // Auto-submit form when filters change
        form.submit();
    }
}

/**
 * Debounce function to limit API calls
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Animate coin balance numbers
 */
function animateCoinBalance() {
    const coinElements = document.querySelectorAll('[data-coin-value]');
    
    coinElements.forEach(element => {
        const targetValue = parseInt(element.getAttribute('data-coin-value') || element.textContent);
        if (isNaN(targetValue)) return;
        
        animateNumber(element, 0, targetValue, 1000);
    });
}

/**
 * Animate number counting up
 */
function animateNumber(element, start, end, duration) {
    const startTime = performance.now();
    
    function updateNumber(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const current = Math.floor(start + (end - start) * progress);
        element.textContent = current;
        
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        }
    }
    
    requestAnimationFrame(updateNumber);
}

/**
 * Enhance item cards with additional interactions
 */
function enhanceItemCards() {
    const itemCards = document.querySelectorAll('.item-card');
    
    itemCards.forEach(card => {
        // Add loading state for buttons
        const buttons = card.querySelectorAll('a[href*="redeem"], a[href*="swap"]');
        buttons.forEach(button => {
            button.addEventListener('click', function(e) {
                if (!this.hasAttribute('data-confirm') || confirm(this.getAttribute('data-confirm'))) {
                    this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
                    this.classList.add('disabled');
                }
            });
        });
        
        // Quick view functionality
        const quickViewBtn = document.createElement('button');
        quickViewBtn.className = 'btn btn-sm btn-outline-secondary position-absolute top-0 start-0 m-2';
        quickViewBtn.innerHTML = '<i data-feather="eye" style="width: 14px; height: 14px;"></i>';
        quickViewBtn.style.opacity = '0';
        quickViewBtn.style.transition = 'opacity 0.3s ease';
        
        card.addEventListener('mouseenter', () => {
            quickViewBtn.style.opacity = '1';
        });
        
        card.addEventListener('mouseleave', () => {
            quickViewBtn.style.opacity = '0';
        });
        
        const cardImage = card.querySelector('.position-relative');
        if (cardImage) {
            cardImage.style.position = 'relative';
            cardImage.appendChild(quickViewBtn);
        }
    });
}

/**
 * Enhance admin forms with better UX
 */
function enhanceAdminForms() {
    const adminForms = document.querySelectorAll('form[action*="admin"]');
    
    adminForms.forEach(form => {
        const coinInput = form.querySelector('input[name="coin_value"]');
        if (coinInput) {
            // Add helpful suggestions
            const suggestions = [5, 10, 15, 20, 25, 30];
            const suggestionContainer = document.createElement('div');
            suggestionContainer.className = 'mt-1';
            
            suggestions.forEach(value => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'btn btn-outline-secondary btn-sm me-1 mb-1';
                btn.textContent = value;
                btn.onclick = () => {
                    coinInput.value = value;
                    coinInput.focus();
                };
                suggestionContainer.appendChild(btn);
            });
            
            coinInput.parentNode.appendChild(suggestionContainer);
        }
        
        // Confirmation for reject actions
        const rejectButtons = form.querySelectorAll('a[href*="reject"]');
        rejectButtons.forEach(btn => {
            btn.addEventListener('click', function(e) {
                if (!confirm('Are you sure you want to reject this item? This action cannot be undone.')) {
                    e.preventDefault();
                }
            });
        });
    });
}

/**
 * Enhance navigation with active states and smooth transitions
 */
function enhanceNavigation() {
    // Highlight current page in navigation
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.includes(href) && href !== '/') {
            link.classList.add('active', 'fw-bold');
        }
    });
    
    // Smooth scroll for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Add loading states to navigation links
    const mainNavLinks = document.querySelectorAll('.navbar-nav .nav-link[href]:not([href^="#"])');
    mainNavLinks.forEach(link => {
        link.addEventListener('click', function() {
            // Add subtle loading indication
            this.style.opacity = '0.7';
        });
    });
}

/**
 * Utility function to show toast notifications
 */
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

/**
 * Create toast container if it doesn't exist
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    container.style.zIndex = '1055';
    document.body.appendChild(container);
    return container;
}

/**
 * Handle AJAX form submissions
 */
function submitFormAjax(form, onSuccess, onError) {
    const formData = new FormData(form);
    
    fetch(form.action, {
        method: form.method,
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            onSuccess(data);
        } else {
            onError(data.error || 'An error occurred');
        }
    })
    .catch(error => {
        onError('Network error occurred');
    });
}

/**
 * Initialize lazy loading for images
 */
function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

/**
 * Handle keyboard shortcuts
 */
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('input[name="query"]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
            const modalInstance = bootstrap.Modal.getInstance(openModal);
            if (modalInstance) {
                modalInstance.hide();
            }
        }
    }
});

// Initialize lazy loading when DOM is ready
if ('IntersectionObserver' in window) {
    initLazyLoading();
}

// Global error handler
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
    // Could send error reports to logging service here
});

// Re-initialize Feather icons after dynamic content changes
function refreshFeatherIcons() {
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

// Export functions for use in other scripts
window.ReWear = {
    showToast,
    submitFormAjax,
    refreshFeatherIcons,
    debounce
};
