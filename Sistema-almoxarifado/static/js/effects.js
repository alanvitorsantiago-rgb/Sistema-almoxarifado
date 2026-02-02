/**
 * FUTURISTIC EFFECTS - SERCO ENGENHARIA ALMOXARIFADO
 * Additional JavaScript effects for enhanced UX
 */

(function () {
    'use strict';

    // ============================================
    // 1. SMOOTH SCROLL TO TOP BUTTON
    // ============================================

    function createScrollToTopButton() {
        const button = document.createElement('button');
        button.innerHTML = '<i class="fas fa-chevron-up"></i>';
        button.className = 'scroll-to-top';
        button.style.cssText = `
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: var(--bg-card);
            border: 2px solid var(--neon-cyan);
            color: var(--neon-cyan);
            font-size: 1.2rem;
            cursor: pointer;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
            z-index: 1000;
            box-shadow: var(--glow-cyan);
            backdrop-filter: blur(10px);
        `;

        button.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });

        window.addEventListener('scroll', () => {
            if (window.pageYOffset > 300) {
                button.style.opacity = '1';
                button.style.visibility = 'visible';
            } else {
                button.style.opacity = '0';
                button.style.visibility = 'hidden';
            }
        });

        button.addEventListener('mouseenter', () => {
            // Removed scale transform for performance
            button.style.boxShadow = 'var(--glow-cyan-strong)';
        });

        button.addEventListener('mouseleave', () => {
            // Removed scale transform for performance
            button.style.boxShadow = 'var(--glow-cyan)';
        });

        document.body.appendChild(button);
    }

    // ============================================
    // 2. TABLE ROW ANIMATIONS (DISABLED FOR PERFORMANCE)
    // ============================================

    function animateTableRows() {
        // DISABLED: Causing performance issues and unwanted movement
        return;
    }

    // ============================================
    // 3. SEARCH INPUT ENHANCEMENTS
    // ============================================

    function enhanceSearchInput() {
        const searchInput = document.querySelector('input[name="q"]');
        if (!searchInput) return;

        // Add clear button
        const clearBtn = document.createElement('button');
        clearBtn.type = 'button';
        clearBtn.innerHTML = '<i class="fas fa-times"></i>';
        clearBtn.className = 'btn btn-sm';
        clearBtn.style.cssText = `
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            background: transparent;
            border: none;
            color: var(--neon-red);
            opacity: 0;
            transition: all 0.3s ease;
            cursor: pointer;
            z-index: 10;
        `;

        clearBtn.addEventListener('click', () => {
            searchInput.value = '';
            searchInput.focus();
            clearBtn.style.opacity = '0';
        });

        searchInput.addEventListener('input', () => {
            clearBtn.style.opacity = searchInput.value ? '1' : '0';
        });

        const inputGroup = searchInput.closest('.input-group');
        if (inputGroup) {
            inputGroup.style.position = 'relative';
            inputGroup.appendChild(clearBtn);

            if (searchInput.value) {
                clearBtn.style.opacity = '1';
            }
        }
    }

    // ============================================
    // 4. LOADING OVERLAY
    // ============================================

    function createLoadingOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 8, 20, 0.95);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            backdrop-filter: blur(10px);
        `;

        overlay.innerHTML = `
            <div style="text-align: center;">
                <div class="loading-spinner" style="margin: 0 auto 20px;"></div>
                <p style="color: var(--neon-cyan); font-family: 'Orbitron', sans-serif; letter-spacing: 0.1em;">
                    CARREGANDO...
                </p>
            </div>
        `;

        document.body.appendChild(overlay);

        // Show loading on form submit
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', () => {
                overlay.style.display = 'flex';
            });
        });
    }

    // ============================================
    // 5. TOOLTIP ENHANCEMENTS
    // ============================================

    function enhanceTooltips() {
        // Custom tooltip styling
        const style = document.createElement('style');
        style.textContent = `
            .tooltip-inner {
                background: var(--bg-card) !important;
                border: 2px solid var(--neon-cyan) !important;
                color: var(--neon-cyan) !important;
                font-family: 'Rajdhana', sans-serif !important;
                font-weight: 600 !important;
                letter-spacing: 0.05em !important;
                box-shadow: var(--glow-cyan) !important;
                backdrop-filter: blur(10px) !important;
            }
            .tooltip.bs-tooltip-top .tooltip-arrow::before {
                border-top-color: var(--neon-cyan) !important;
            }
            .tooltip.bs-tooltip-bottom .tooltip-arrow::before {
                border-bottom-color: var(--neon-cyan) !important;
            }
            .tooltip.bs-tooltip-start .tooltip-arrow::before {
                border-left-color: var(--neon-cyan) !important;
            }
            .tooltip.bs-tooltip-end .tooltip-arrow::before {
                border-right-color: var(--neon-cyan) !important;
            }
        `;
        document.head.appendChild(style);
    }

    // ============================================
    // 6. CARD HOVER 3D EFFECT (DISABLED FOR PERFORMANCE)
    // ============================================

    function add3DCardEffect() {
        // DISABLED: Causing unwanted movement on hover
        return;
    }

    // ============================================
    // 7. NOTIFICATION SYSTEM
    // ============================================

    window.showNotification = function (message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert-futuristic alert-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 30px;
            min-width: 300px;
            max-width: 400px;
            z-index: 9998;
            animation: slideInRight 0.5s ease;
        `;
        notification.innerHTML = `
            <div class="d-flex align-items-center justify-content-between">
                <span>${message}</span>
                <button type="button" class="btn-close btn-close-white ms-3" aria-label="Close"></button>
            </div>
        `;

        document.body.appendChild(notification);

        notification.querySelector('.btn-close').addEventListener('click', () => {
            notification.style.animation = 'slideOutRight 0.5s ease';
            setTimeout(() => notification.remove(), 500);
        });

        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.5s ease';
            setTimeout(() => notification.remove(), 500);
        }, 5000);
    };

    // Add animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);

    // ============================================
    // INITIALIZE ALL EFFECTS
    // ============================================

    document.addEventListener('DOMContentLoaded', function () {
        createScrollToTopButton();
        animateTableRows();
        enhanceSearchInput();
        createLoadingOverlay();
        enhanceTooltips();
        add3DCardEffect();

        console.log('%c🚀 SERCO ENGENHARIA Almoxarifado - Futuristic UI Loaded',
            'color: #00f5ff; font-size: 16px; font-weight: bold; text-shadow: 0 0 10px #00f5ff;');
    });

})();
