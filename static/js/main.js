// Main JavaScript functionality

class VendorApp {
    constructor() {
        this.init();
    }

    init() {
        this.initializeLoading();
        this.initializeNavigation();
        this.initializeFlashMessages();
        this.initializeServiceWorker();
        this.initializePerformanceMonitoring();
    }

    initializeLoading() {
        // Show loading spinner initially
        const spinner = document.getElementById('loading-spinner');
        
        // Hide spinner when page is fully loaded
        window.addEventListener('load', () => {
            setTimeout(() => {
                spinner.classList.add('hidden');
                
                // Remove from DOM after animation
                setTimeout(() => {
                    spinner.remove();
                }, 300);
            }, 500);
        });

        // Fallback: hide spinner after 3 seconds max
        setTimeout(() => {
            spinner.classList.add('hidden');
        }, 3000);
    }

    initializeNavigation() {
        const navToggle = document.getElementById('nav-toggle');
        const navMenu = document.getElementById('nav-menu');

        if (navToggle && navMenu) {
            navToggle.addEventListener('click', () => {
                navToggle.classList.toggle('active');
                navMenu.classList.toggle('active');
            });

            // Close mobile menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
                    navToggle.classList.remove('active');
                    navMenu.classList.remove('active');
                }
            });

            // Close mobile menu when window is resized to desktop size
            window.addEventListener('resize', () => {
                if (window.innerWidth > 768) {
                    navToggle.classList.remove('active');
                    navMenu.classList.remove('active');
                }
            });
        }
    }

    initializeFlashMessages() {
        const flashMessages = document.querySelectorAll('.flash-message');
        
        flashMessages.forEach(message => {
            const closeBtn = message.querySelector('.flash-close');
            
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    message.style.animation = 'slideOut 0.3s ease forwards';
                    setTimeout(() => {
                        message.remove();
                    }, 300);
                });
            }

            // Auto-remove flash messages after 5 seconds
            setTimeout(() => {
                if (message.parentNode) {
                    message.style.animation = 'slideOut 0.3s ease forwards';
                    setTimeout(() => {
                        message.remove();
                    }, 300);
                }
            }, 5000);
        });
    }

    initializeServiceWorker() {
        // Service worker registration is handled in base.html
        // Additional service worker functionality can be added here
    }

    initializePerformanceMonitoring() {
        // Monitor page performance
        if ('performance' in window) {
            window.addEventListener('load', () => {
                const perfData = window.performance.timing;
                const loadTime = perfData.loadEventEnd - perfData.navigationStart;
                
                console.log(`Page loaded in ${loadTime}ms`);
                
                // Send to analytics if needed
                if (loadTime > 3000) {
                    console.warn('Page load time is slow:', loadTime);
                }
            });
        }
    }

    // Utility function for API calls
    async apiCall(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };

        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, mergedOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            return { success: true, data };
        } catch (error) {
            console.error('API call failed:', error);
            return { success: false, error: error.message };
        }
    }

    // Format currency for Tanzania
    formatCurrency(amount) {
        return new Intl.NumberFormat('sw-TZ', {
            style: 'currency',
            currency: 'TZS',
            minimumFractionDigits: 0
        }).format(amount);
    }

    // Format phone number for display
    formatPhoneNumber(phone) {
        if (!phone) return '';
        const cleaned = phone.toString().replace(/\D/g, '');
        if (cleaned.length === 12 && cleaned.startsWith('255')) {
            return `+${cleaned}`;
        }
        return phone;
    }

    // Debounce function for search inputs
    debounce(func, wait) {
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

    // Show notification
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button class="notification-close">&times;</button>
        `;

        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${this.getNotificationColor(type)};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            z-index: 10000;
            display: flex;
            align-items: center;
            gap: 1rem;
            animation: slideInRight 0.3s ease;
        `;

        document.body.appendChild(notification);

        // Add close functionality
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            notification.style.animation = 'slideOutRight 0.3s ease forwards';
            setTimeout(() => notification.remove(), 300);
        });

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOutRight 0.3s ease forwards';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }

    getNotificationColor(type) {
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };
        return colors[type] || colors.info;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.vendorApp = new VendorApp();
});

// Add CSS animations for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes slideOutRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }

    @keyframes slideOut {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(-10px);
        }
    }
`;
document.head.appendChild(style);