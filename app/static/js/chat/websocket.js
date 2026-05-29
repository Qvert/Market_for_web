/**
 * Модуль ChatClient
 * Отвечает ТОЛЬКО за транспортный слой (WebSocket соединение).
 */
class ChatClient {
    constructor(url, token = null) {
        this.baseUrl = url;
        this.token = token;
        this.ws = null;
        this.listeners = {};

        this.reconnectAttempts = 0;
        this.baseDelay = 1000;
        this.maxDelay = 30000;
        this.intentionalClose = false;
    }

    get _reconnectDelay() {
        return Math.min(this.baseDelay * Math.pow(2, this.reconnectAttempts), this.maxDelay);
    }

    get _wsUrl() {
        return this.token ? `${this.baseUrl}?token=${this.token}` : this.baseUrl;
    }

    connect() {
        this.intentionalClose = false;
        this._emit('system', { type: 'connecting', message: 'Подключение...' });

        this.ws = new WebSocket(this._wsUrl);

        this.ws.onopen = () => {
            this.reconnectAttempts = 0;
            this._emit('system', { type: 'connected', message: 'Соединение установлено' });
        };

        this.ws.onmessage = ({ data }) => {
            try {
                const parsed = JSON.parse(data);
                this._emit(parsed.event, parsed.data);
            } catch (e) {
                console.error('[ChatClient] Ошибка парсинга:', e);
            }
        };

        this.ws.onclose = (e) => {
            if (this.intentionalClose) return;
            this._emit('system', { type: 'disconnected', message: `Связь потеряна` });
            this._scheduleReconnect();
        };
    }

    _scheduleReconnect() {
        const delay = this._reconnectDelay;
        this.reconnectAttempts++;
        setTimeout(() => { if (!this.intentionalClose) this.connect(); }, delay);
    }

    on(event, callback) {
        if (!this.listeners[event]) this.listeners[event] = [];
        this.listeners[event].push(callback);
        return this;
    }

    _emit(event, data) {
        (this.listeners[event] || []).forEach(cb => cb(data));
    }

    send(event, data = {}) {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ event, data }));
            return true;
        }
        return false;
    }

    disconnect() {
        this.intentionalClose = true;
        if (this.ws) this.ws.close();
    }
}

/**
 * Модуль NotificationManager
 * Реализует WebSocket уведомления + Сторонний сервис Push (ntfy.sh)
 */
class NotificationManager {
    constructor(wsUrl, userId = null, token = null) {
        this.wsUrl = token ? `${wsUrl}?token=${token}` : wsUrl;
        // Очищаем userId (email) от спецсимволов для топика ntfy
        this.userId = userId ? userId.replace(/[^a-zA-Z0-9]/g, '_') : null;
        this.ws = null;
        this.eventSource = null;
        this.swRegistration = null;
        this.permission = Notification.permission;
        this.reconnectAttempts = 0;
        this.intentionalClose = false;

        this._createToastContainer();
    }

    async init() {
        await this._registerServiceWorker();
        await this._requestPermission();
        this._connect(); // WebSocket
        if (this.userId) {
            this._subscribeToExternalPush(); // ntfy.sh
        }
    }

    // --- Исправлено: Регистрация Service Worker ---
    async _registerServiceWorker() {
        if (!('serviceWorker' in navigator)) return;
        try {
            // Исправлена опечатка: navigator.serviceWorker вместо navigator.worker
            this.swRegistration = await navigator.serviceWorker.register('/static/js/sw.js', { scope: '/' });
            console.log('[Notifications] Service Worker готов');
        } catch (error) {
            console.error('[Notifications] SW Error:', error);
        }
    }

    async _requestPermission() {
        if ('Notification' in window && this.permission === 'default') {
            this.permission = await Notification.requestPermission();
        }
    }

    // --- Сторонний сервис Push (Задание) ---
    _subscribeToExternalPush() {
        const topic = `ntfy_user_${this.userId}`;
        const ntfyUrl = `https://ntfy.sh/${topic}/sse`;

        console.log(`[Notifications] Подписка на ntfy: ${topic}`);
        this.eventSource = new EventSource(ntfyUrl);

        this.eventSource.onmessage = (event) => {
            if (!event.data) return; // Игнорируем пустые keep-alive сообщения

            try {
                const payload = JSON.parse(event.data);
                // ntfy присылает разные типы событий, нам нужно только 'message'
                if (payload.event !== 'message') return;

                const notification = {
                    title: payload.title || "Уведомление",
                    body: payload.message || "",
                    type: 'info',
                    ts: new Date().toISOString(),
                    url: payload.click || '/'
                };

                console.log('[Notifications] Получен Push от ntfy');
                this._handleNotification(notification);
            } catch (e) {
                console.error('[Notifications] ntfy error:', e);
            }
        };
    }

    _connect() {
        this.ws = new WebSocket(this.wsUrl);
        this.ws.onopen = () => { this.reconnectAttempts = 0; };
        this.ws.onmessage = ({ data }) => {
            const { event, data: payload } = JSON.parse(data);
            if (event === 'push_notification') this._handleNotification(payload);
        };
        this.ws.onclose = () => {
            if (!this.intentionalClose) {
                const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts++), 30000);
                setTimeout(() => this._connect(), delay);
            }
        };
    }

    _handleNotification(notification) {
        // 1. Системный Push (через SW)
        if (this.permission === 'granted' && this.swRegistration) {
            navigator.serviceWorker.ready.then(reg => {
                reg.showNotification(notification.title, {
                    body: notification.body,
                    icon: '/static/img/logo.png',
                    data: { url: notification.url }
                });
            });
        }
        // 2. Всплывающий тост на сайте
        this._showToast(notification);
        this._updateFabBadge();
    }

    _createToastContainer() {
        if (document.getElementById('toast-container')) return;
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = `position:fixed; top:80px; right:20px; z-index:9999; display:flex; flex-direction:column; gap:10px; pointer-events:none;`;
        document.body.appendChild(container);
    }

    _showToast(notification) {
        const container = document.getElementById('toast-container');
        const colors = { success: '#10b981', error: '#ef4444', info: '#3b82f6', warning: '#f59e0b' };
        const color = colors[notification.type] || colors.info;

        const toast = document.createElement('div');
        toast.style.cssText = `background:${color}; color:white; border-radius:12px; padding:14px; box-shadow:0 4px 12px rgba(0,0,0,0.15); pointer-events:all; cursor:pointer; animation:slideIn 0.3s ease; min-width:250px;`;
        toast.innerHTML = `
            <div style="font-weight:bold; font-size:14px;">${notification.title}</div>
            <div style="font-size:13px; margin-top:4px;">${notification.body}</div>
        `;

        toast.onclick = () => { if (notification.url) window.location.href = notification.url; };
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }

    _updateFabBadge() {
        const fab = document.getElementById('fab-badge');
        if (fab) {
            fab.textContent = parseInt(fab.textContent || '0') + 1;
            fab.style.display = 'block';
        }
    }
}

// Добавляем стили анимации
const styleTag = document.createElement('style');
styleTag.textContent = `
    @keyframes slideIn { from { transform: translateX(120%); } to { transform: translateX(0); } }
    @keyframes slideOut { from { transform: translateX(0); } to { transform: translateX(120%); } }
`;
document.head.appendChild(styleTag);