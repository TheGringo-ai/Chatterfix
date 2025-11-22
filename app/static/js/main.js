// Unified CMMS JavaScript Functions

// Global notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `cmms-notification cmms-notification-${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" style="margin-left: 1rem; background: none; border: none; color: inherit; cursor: pointer;">×</button>
    `;
    notification.style.cssText = `
        position: fixed; top: 2rem; right: 2rem; z-index: 10000;
        background: rgba(0,0,0,0.9); color: white; padding: 1rem 1.5rem;
        border-radius: 8px; backdrop-filter: blur(10px);
        border-left: 4px solid ${type === 'success' ? '#38ef7d' : type === 'warning' ? '#fbbf24' : type === 'error' ? '#ff4757' : '#74b9ff'};
        animation: slideIn 0.3s ease;
    `;
    document.body.appendChild(notification);

    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Enhanced modal system
function showModal(title, content, actions = []) {
    const modal = document.createElement('div');
    modal.className = 'cmms-modal';
    modal.innerHTML = `
        <div class="cmms-modal-backdrop" onclick="closeModal()">
            <div class="cmms-modal-content" onclick="event.stopPropagation()">
                <div class="cmms-modal-header">
                    <h3>${title}</h3>
                    <button onclick="closeModal()" class="cmms-modal-close">×</button>
                </div>
                <div class="cmms-modal-body">${content}</div>
                <div class="cmms-modal-actions">
                    ${actions.map(action => `<button class="cmms-btn ${action.class || ''}" onclick="${action.onclick}">${action.text}</button>`).join('')}
                </div>
            </div>
        </div>
    `;
    modal.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 10001;
        display: flex; align-items: center; justify-content: center;
    `;
    document.body.appendChild(modal);

    // Add modal styles if not present
    if (!document.getElementById('modal-styles')) {
        const style = document.createElement('style');
        style.id = 'modal-styles';
        style.textContent = `
            .cmms-modal-backdrop {
                position: absolute; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0,0,0,0.7); backdrop-filter: blur(5px);
            }
            .cmms-modal-content {
                background: rgba(255,255,255,0.15); backdrop-filter: blur(15px);
                border-radius: 15px; border: 1px solid rgba(255,255,255,0.2);
                max-width: 600px; width: 90%; max-height: 80%; overflow-y: auto;
                color: white;
            }
            .cmms-modal-header {
                padding: 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.1);
                display: flex; justify-content: space-between; align-items: center;
            }
            .cmms-modal-header h3 { margin: 0; }
            .cmms-modal-close {
                background: none; border: none; color: white; font-size: 1.5rem;
                cursor: pointer; padding: 0.5rem;
            }
            .cmms-modal-body { padding: 1.5rem; }
            .cmms-modal-actions { 
                padding: 1.5rem; border-top: 1px solid rgba(255,255,255,0.1);
                display: flex; justify-content: flex-end; gap: 1rem;
            }
        `;
        document.head.appendChild(style);
    }

    window.currentModal = modal;
}

function closeModal() {
    if (window.currentModal) {
        document.body.removeChild(window.currentModal);
        window.currentModal = null;
    }
}

// Loading states
function showLoading(element) {
    element.classList.add('loading');
    element.style.pointerEvents = 'none';
}

function hideLoading(element) {
    element.classList.remove('loading');
    element.style.pointerEvents = 'auto';
}

// Enhanced search and filter
function setupUnifiedFiltering(containerId, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const items = container.querySelectorAll(options.itemSelector || '.item-card');

    function filterItems() {
        const filters = options.filters || {};

        items.forEach(item => {
            let showItem = true;

            Object.keys(filters).forEach(filterKey => {
                const filterValue = document.getElementById(filters[filterKey])?.value?.toLowerCase();
                const itemValue = item.dataset[filterKey]?.toLowerCase();

                if (filterValue && itemValue && !itemValue.includes(filterValue)) {
                    showItem = false;
                }
            });

            // Text search
            const searchInput = document.getElementById(options.searchId);
            if (searchInput && searchInput.value) {
                const searchTerm = searchInput.value.toLowerCase();
                const itemText = item.textContent.toLowerCase();
                if (!itemText.includes(searchTerm)) {
                    showItem = false;
                }
            }

            item.style.display = showItem ? 'block' : 'none';
        });

        // Update count if counter exists
        const counter = document.getElementById(options.counterId);
        if (counter) {
            const visibleCount = Array.from(items).filter(item => item.style.display !== 'none').length;
            counter.textContent = `Showing ${visibleCount} of ${items.length} items`;
        }
    }

    // Bind filter events
    Object.values(options.filters || {}).forEach(filterId => {
        const element = document.getElementById(filterId);
        if (element) {
            element.addEventListener('change', filterItems);
        }
    });

    if (options.searchId) {
        const searchInput = document.getElementById(options.searchId);
        if (searchInput) {
            searchInput.addEventListener('input', filterItems);
        }
    }

    // Initial filter
    filterItems();
}

// Unified form handling
function handleFormSubmit(formId, endpoint, options = {}) {
    const form = document.getElementById(formId);
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;

        try {
            showLoading(submitBtn);
            submitBtn.textContent = 'Processing...';

            const formData = new FormData(form);
            const data = Object.fromEntries(formData);

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                showNotification(options.successMessage || 'Operation completed successfully!', 'success');
                if (options.onSuccess) options.onSuccess(result);
                if (options.redirect) window.location.href = options.redirect;
                if (options.reload) location.reload();
            } else {
                throw new Error(result.message || 'Operation failed');
            }
        } catch (error) {
            showNotification(error.message || 'An error occurred', 'error');
            if (options.onError) options.onError(error);
        } finally {
            hideLoading(submitBtn);
            submitBtn.textContent = originalText;
        }
    });
}
