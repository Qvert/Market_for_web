/**
 * Класс ChatClient для управления WebSocket соединением
 * Реализует паттерн Event Emitter, экспоненциальное переподключение и отправку событий.
 */
class ChatClient {
    constructor(url, token = null) {
        this.url = token ? `${url}?token=${token}` : url;
        this.ws = null;
        this.eventListeners = {};

        // Настройки переподключения (Экспоненциальная задержка)
        this.reconnectAttempts = 0;
        this.baseDelay = 1000; // 1 секунда
        this.maxDelay = 15000; // Максимум 15 секунд
        this.isIntentionalDisconnect = false;
    }

    // Подключение к серверу
    connect() {
        this.isIntentionalDisconnect = false;
        this._triggerEvent('system', { type: 'connecting', message: 'Подключение к серверу...' });

        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
            this.reconnectAttempts = 0;
            this._triggerEvent('system', { type: 'connected', message: 'Соединение установлено' });
        };

        this.ws.onmessage = (event) => {
            const parsed = JSON.parse(event.data);
            this._triggerEvent(parsed.event, parsed.data);
        };

        this.ws.onclose = (event) => {
            if (this.isIntentionalDisconnect) return;

            this._triggerEvent('system', { type: 'disconnected', message: 'Соединение потеряно' });
            this._handleReconnect();
        };

        this.ws.onerror = (error) => {
            this._triggerEvent('system', { type: 'error', message: 'Ошибка сети' });
            this.ws.close();
        };
    }

    // Экспоненциальное переподключение (Пункт 3.2)
    _handleReconnect() {
        const delay = Math.min(this.baseDelay * Math.pow(2, this.reconnectAttempts), this.maxDelay);
        this.reconnectAttempts++;

        this._triggerEvent('system', {
            type: 'reconnecting',
            message: `Переподключение через ${delay / 1000} сек... (Попытка ${this.reconnectAttempts})`
        });

        setTimeout(() => this.connect(), delay);
    }

    // Отправка данных на сервер
    send(event, data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ event: event, data: data }));
        } else {
            console.error("WebSocket не готов к отправке данных");
        }
    }

    // Подписка на события от сервера
    on(event, callback) {
        if (!this.eventListeners[event]) {
            this.eventListeners[event] = [];
        }
        this.eventListeners[event].push(callback);
    }

    // Вызов обработчиков
    _triggerEvent(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => callback(data));
        }
    }

    disconnect() {
        this.isIntentionalDisconnect = true;
        if (this.ws) this.ws.close();
    }
}