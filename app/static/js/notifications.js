class NotificationManager {
    constructor(wsUrl, userId = null, token = null) {
        this.wsUrl = token ? `${wsUrl}?token=${token}` : wsUrl;

        // Очищаем userId (если это email), так как ntfy лучше работает с простыми строками
        this.userId = userId ? userId.replace(/[^a-zA-Z0-9]/g, '_') : null;

        this.ws = null;
        this.eventSource = null;
        this.swRegistration = null;
        this.permission = Notification.permission;
        this.reconnectAttempts = 0;
        this.intentionalClose = false;

        this._createToastContainer();
    }

    // ------------------------------------------------------------------
    // Инициализация
    // ------------------------------------------------------------------

    async init() {
        await this._registerServiceWorker();
        await this._requestPermission();

        // 1. Подключаем основной WebSocket
        this._connect();

        // 2. Подключаем сторонний сервис Push (ntfy.sh)
        if (this.userId) {
            this._subscribeToExternalPush();
        }
    }

    // ------------------------------------------------------------------
    // Сторонний сервис Push (ntfy.sh) - ИСПРАВЛЕНО
    // ------------------------------------------------------------------

    _subscribeToExternalPush() {
        const topic = `ntfy_user_${this.userId}`;
        // Используем SSE для получения уведомлений в реальном времени
        const ntfyUrl = `https://ntfy.sh/${topic}/sse`;

        console.log(`[Notifications] Подписка на сторонний сервис: ${topic}`);
        this.eventSource = new EventSource(ntfyUrl);

        this.eventSource.onmessage = (event) => {
            if (!event.data) return; // Пропускаем пустые keep-alive сообщения

            try {
                const payload = JSON.parse(event.data);

                // ntfy присылает системные события (open, keep-alive), нам нужны только сообщения
                if (payload.event !== 'message') return;

                const notification = {
                    id: payload.id || Math.random().toString(36).substr(2, 9),
                    title: payload.title || "Уведомление",
                    body: payload.message || "",
                    type: 'info',
                    ts: new Date().toISOString(),
                    url: payload.click || '/'
                };

                console.log('[Notifications] Получен Push от стороннего сервера (ntfy)');
                this._handleNotification(notification);
            } catch (e) {
                console.error('[Notifications] Ошибка парсинга ntfy:', e);
            }
        };

        this.eventSource.onerror = () => {
            console.warn('[Notifications] Ошибка ntfy, переподключение...');
        };
    }

    // ------------------------------------------------------------------
    // Service Worker - ИСПРАВЛЕНО (navigator.serviceWorker)
    // ------------------------------------------------------------------

    async _registerServiceWorker() {
        if (!('serviceWorker' in navigator)) {
            console.warn('[Notifications] Service Worker не поддерживается');
            return;
        }

        try {
            // Исправлена опечатка navigator.worker -> navigator.serviceWorker
            this.swRegistration = await navigator.serviceWorker.register(
                '/static/js/sw.js',
                { scope: '/' }
            );
            console.log('[Notifications] Service Worker зарегистрирован');
        } catch (error) {
            console.error('[Notifications] Ошибка регистрации SW:', error);
        }
    }

    async _requestPermission() {
        if (!('Notification' in window)) return;

        if (this.permission === 'default') {
            this.permission = await Notification.requestPermission();
            console.log(`[Notifications] Права: ${this.permission}`);
        }
    }

    // ------------------------------------------------------------------
    // WebSocket подключение
    // ------------------------------------------------------------------

    _connect() {
        this.intentionalClose = false;
        this.ws = new WebSocket(this.wsUrl);

        this.ws.onopen = () => {
            this.reconnectAttempts = 0;
            console.log('[Notifications] WebSocket подключён');
        };

        this.ws.onmessage = ({ data }) => {
            try {
                const { event, data: payload } = JSON.parse(data);
                if (event === 'push_notification') {
                    this._handleNotification(payload);
                }
            } catch (e) {
                console.error('[Notifications] WS parse error:', e);
            }
        };

        this.ws.onclose = () => {
            if (this.intentionalClose) return;
            this._scheduleReconnect();
        };
    }

    _scheduleReconnect() {
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts++), 30000);
        setTimeout(() => { if (!this.intentionalClose) this._connect(); }, delay);
    }

    unsubscribe() {
        this.intentionalClose = true;
        if (this.ws) this.ws.close();
        if (this.eventSource) this.eventSource.close();
    }

    // ------------------------------------------------------------------
    // Обработка уведомления (Системный Push + UI Тост)
    // ------------------------------------------------------------------

    _handleNotification(notification) {
        // 1. Системное уведомление через браузер
        if (this.permission === 'granted') {
            // Показываем через Service Worker, чтобы работало в фоне
            navigator.serviceWorker.ready.then(registration => {
                registration.showNotification(notification.title, {
                    body: notification.body,
                    icon: '/static/img/logo.png',
                    data: { url: notification.url }
                });
            });
        }

        // 2. UI тост внутри сайта
        this._showToast(notification);
        this._updateFabBadge();
    }

    // ------------------------------------------------------------------
    // UI Тост-уведомления
    // ------------------------------------------------------------------

    _createToastContainer() {
        if (document.getElementById('toast-container')) return;
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = `
            position: fixed; top: 80px; right: 20px; z-index: 9999;
            display: flex; flex-direction: column; gap: 10px; max-width: 360px; pointer-events: none;
        `;
        document.body.appendChild(container);
    }

    _showToast(notification) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const colors = {
            success: '#10b981', error: '#ef4444', info: '#3b82f6', warning: '#f59e0b'
        };
        const color = colors[notification.type] || colors.info;

        const toast = document.createElement('div');
        toast.style.cssText = `
            background: ${color}; color: white; border-radius: 12px; padding: 14px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15); pointer-events: all; cursor: pointer;
            animation: slideIn 0.3s ease; min-width: 250px;
        `;
        toast.innerHTML = `
            <div style="font-weight:700; font-size:14px;">${notification.title}</div>
            <div style="font-size:13px; opacity:0.9; margin-top:4px;">${notification.body}</div>
        `;

        toast.onclick = () => {
            if (notification.url && notification.url !== '/') window.location.href = notification.url;
            toast.remove();
        };

        container.appendChild(toast);
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        }, 6000);
    }

    _updateFabBadge() {
        const fab = document.getElementById('fab-badge');
        if (fab) {
            const current = parseInt(fab.textContent || '0');
            fab.textContent = current + 1;
            fab.style.display = 'block';
        }
    }
}

const styleTag = document.createElement('style');
styleTag.textContent = `
    @keyframes slideIn { from { transform: translateX(120%); } to { transform: translateX(0); } }
    @keyframes slideOut { from { transform: translateX(0); } to { transform: translateX(120%); } }
`;
document.head.appendChild(styleTag);