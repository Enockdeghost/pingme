// Theme management functionality

class ThemeManager {
    constructor() {
        this.currentTheme = this.getStoredTheme() || 'dark-blue';
        this.init();
    }

    init() {
        this.applyTheme(this.currentTheme);
        this.initializeThemeToggle();
        this.initializeSystemPreference();
    }

    getStoredTheme() {
        try {
            return localStorage.getItem('vendorapp-theme');
        } catch (error) {
            console.warn('Could not access localStorage:', error);
            return null;
        }
    }

    setStoredTheme(theme) {
        try {
            localStorage.setItem('vendorapp-theme', theme);
        } catch (error) {
            console.warn('Could not save theme to localStorage:', error);
        }
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
        this.setStoredTheme(theme);
        this.updateToggleButton(theme);
    }

    initializeThemeToggle() {
        const toggleButton = document.getElementById('theme-toggle');
        
        if (toggleButton) {
            toggleButton.addEventListener('click', () => {
                this.toggleTheme();
            });
        }

        this.updateToggleButton(this.currentTheme);
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'dark-blue' ? 'light' : 'dark-blue';
        this.applyTheme(newTheme);
        
        // Dispatch custom event for theme change
        window.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme: newTheme }
        }));
    }

    updateToggleButton(theme) {
        const toggleButton = document.getElementById('theme-toggle');
        if (!toggleButton) return;

        const icon = toggleButton.querySelector('i');
        if (icon) {
            if (theme === 'dark-blue') {
                icon.className = 'fas fa-moon';
                toggleButton.setAttribute('aria-label', 'Switch to light theme');
            } else {
                icon.className = 'fas fa-sun';
                toggleButton.setAttribute('aria-label', 'Switch to dark theme');
            }
        }
    }

    initializeSystemPreference() {
        // Check if user has a system preference
        if (this.getStoredTheme()) return; // Don't override user choice

        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const systemTheme = prefersDark ? 'dark-blue' : 'light';
        
        this.applyTheme(systemTheme);

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!this.getStoredTheme()) { // Only auto-change if user hasn't set a preference
                const newSystemTheme = e.matches ? 'dark-blue' : 'light';
                this.applyTheme(newSystemTheme);
            }
        });
    }

    // Method to get current theme
    getCurrentTheme() {
        return this.currentTheme;
    }

    // Method to set specific theme
    setTheme(theme) {
        if (['dark-blue', 'light'].includes(theme)) {
            this.applyTheme(theme);
        }
    }
}

// Initialize theme manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}