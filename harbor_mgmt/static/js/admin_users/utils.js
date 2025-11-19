export function getCookie(name) {
    let cookieValue = null;

    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i += 1) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === `${name}=`) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }

    if (!cookieValue) {
        const tokenInput = document.querySelector('[name="csrfmiddlewaretoken"]');
        if (tokenInput) cookieValue = tokenInput.value;
    }

    return cookieValue;
}

export function showNotification(message, type = 'info') {
    const notif = document.createElement('div');
    notif.textContent = message;
    notif.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 8px;
        font-weight: 500;
        z-index: 3000;
        animation: slideIn 0.3s ease-out;
        ${type === 'success'
            ? 'background: #10b981; color: white;'
            : type === 'error'
                ? 'background: #ef4444; color: white;'
                : 'background: #3b82f6; color: white;'}
    `;

    document.body.appendChild(notif);
    setTimeout(() => notif.remove(), 3000);
}
