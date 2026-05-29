/**
 * Модуль управления Push-уведомлениями на клиенте.
 *
 * Отвечает за:
 * 1. Регистрацию Service Worker
 * 2. Запрос разрешения на уведомления
 * 3. WebSocket подключение к /api/notify/subscribe
 * 4. Отображение тост-уведомлений в интерфейсе (UI fallback)
 * 5. Отправку в Service Worker для системных уведомлений
 */
class NotificationManager {
    constructor(wsUrl, token = null) {
        this.wsUrl        = token ? `${wsUrl}?token=${token}` : wsUrl;
        this.ws           = null;
        this.swRegistration = null;
        this.permission   = Notification.permission; // 'default' | 'granted' | 'denied'
        this.reconnectAttempts = 0;
        this.intentionalClose  = false;

        // Контейнер для тостов (создаём при инициализации)
        this._createToastContainer();
    }

    // ------------------------------------------------------------------
    // Инициализация
    // ------------------------------------------------------------------

    async init() {
        // 1. Регистрируем Service Worker
        await this._registerServiceWorker();

        // 2. Запрашиваем разрешение на уведомления
        await this._requestPermission();

        // 3. Подключаемся к WebSocket
        this._connect();
    }

    // ------------------------------------------------------------------
    // Service Worker
    // ------------------------------------------------------------------

    async _registerServiceWorker() {
        if (!('serviceWorker' in navigator)) {
            console.warn('[Notifications] Service Worker не поддерживается браузером');
            return;
        }

        try {
            // SW должен лежать по пути /static/js/sw.js
            this.swRegistration = await navigator.serviceWorker.register(
                '/static/js/sw.js',
                { scope: '/' }  // Область действия — весь сайт
            );
            console.log('[Notifications] Service Worker зарегистрирован');
        } catch (error) {
            console.error('[Notifications] Ошибка регистрации SW:', error);
        }
    }

    async _requestPermission() {
        if (!('Notification' in window)) {
            console.warn('[Notifications] Уведомления не поддерживаются');
            return;
        }

        if (this.permission === 'default') {
            // Спрашиваем пользователя
            this.permission = await Notification.requestPermission();
            console.log(`[Notifications] Разрешение: ${this.permission}`);
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
                } else if (event === 'pong') {
                    console.log('[Notifications] Pong от сервера');
                }
            } catch (e) {
                console.error('[Notifications] Ошибка парсинга:', e);
            }
        };

        this.ws.onclose = () => {
            if (this.intentionalClose) return;
            this._scheduleReconnect();
        };
    }

    _scheduleReconnect() {
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
        this.reconnectAttempts++;
        console.log(`[Notifications] Переподключение через ${delay / 1000}с`);
        setTimeout(() => {
            if (!this.intentionalClose) this._connect();
        }, delay);
    }

    unsubscribe() {
        this.intentionalClose = true;
        if (this.ws) {
            this.ws.send(JSON.stringify({ event: 'unsubscribe', data: {} }));
            this.ws.close();
        }
    }

    // ------------------------------------------------------------------
    // Обработка входящего уведомления (Пункт 3 задания)
    // ------------------------------------------------------------------

    _handleNotification(notification) {
        // Способ 1: Системное уведомление через Service Worker (фоновое, нативное)
        if (this.permission === 'granted' && this.swRegistration) {
            navigator.serviceWorker.ready.then(registration => {
                registration.active?.postMessage({
                    type:         'SHOW_NOTIFICATION',
                    notification: notification,
                });
            });
        }

        // Способ 2: UI тост (всегда, независимо от разрешений)
        // Работает как fallback или дополнение к системным уведомлениям
        this._showToast(notification);

        // Обновляем счётчик на иконке
        this._updateFabBadge();
    }

    // ------------------------------------------------------------------
    // UI Тост-уведомления (стандартный механизм отрисовки)
    // ------------------------------------------------------------------

    _createToastContainer() {
        if (document.getElementById('toast-container')) return;

        const container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 360px;
            pointer-events: none;
        `;
        document.body.appendChild(container);
    }

    _showToast(notification) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        // Цвета по типу уведомления
        const colors = {
            info:    { bg: '#3b82f6', icon: 'ℹ️' },
            success: { bg: '#10b981', icon: '✅' },
            warning: { bg: '#f59e0b', icon: '⚠️' },
            error:   { bg: '#ef4444', icon: '❌' },
            order:   { bg: '#8b5cf6', icon: '📦' },
            promo:   { bg: '#ec4899', icon: '🎉' },
            chat:    { bg: '#0ea5e9', icon: '💬' },
        };

        const style = colors[notification.type] || colors.info;
        const time  = new Date(notification.ts).toLocaleTimeString([], {
            hour: '2-digit', minute: '2-digit'
        });

        const toast = document.createElement('div');
        toast.style.cssText = `
            background: ${style.bg};
            color: white;
            border-radius: 12px;
            padding: 14px 16px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
            pointer-events: all;
            cursor: pointer;
            animation: slideIn 0.3s ease;
            display: flex;
            gap: 12px;
            align-items: flex-start;
            min-width: 280px;
        `;
        toast.innerHTML = `
            <span style="font-size:20px;flex-shrink:0">${style.icon}</span>
            <div style="flex:1;min-width:0">
                <div style="font-weight:700;font-size:14px;margin-bottom:4px">${notification.title}</div>
                <div style="font-size:13px;opacity:0.9;line-height:1.3">${notification.body}</div>
                <div style="font-size:11px;opacity:0.7;margin-top:6px">${time}</div>
            </div>
            <button onclick="this.parentElement.remove()" style="
                background:none;border:none;color:white;cursor:pointer;
                font-size:16px;padding:0;flex-shrink:0;opacity:0.8;line-height:1
            ">✕</button>
        `;

        // Клик по тосту — переходим по url
        toast.addEventListener('click', (e) => {
            if (e.target.tagName === 'BUTTON') return;
            if (notification.url && notification.url !== '/') {
                window.location.href = notification.url;
            }
            toast.remove();
        });

        container.appendChild(toast);

        // Автоудаление через 6 секунд
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        }, 6000);
    }

    _updateFabBadge() {
        // Обновляем бейдж на плавающей кнопке чата (если есть)
        const fab = document.getElementById('fab-badge');
        if (!fab) return;

        const current = parseInt(fab.textContent || '0');
        fab.textContent = current + 1;
        fab.classList.add('visible');
    }
}

// CSS анимации для тостов
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(120%); opacity: 0; }
        to   { transform: translateX(0);   opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0);   opacity: 1; }
        to   { transform: translateX(120%); opacity: 0; }
    }
`;
document.head.appendChild(style);