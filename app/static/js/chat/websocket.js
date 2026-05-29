/**
 * Модуль ChatClient
 * Отвечает ТОЛЬКО за транспортный слой (WebSocket соединение).
 * Не знает ничего про HTML и DOM.
 * Реализует паттерн EventEmitter.
 */
class ChatClient {
    constructor(url, token = null) {
        this.baseUrl = url;
        this.token = token;
        this.ws = null;
        this.listeners = {};

        // Состояние реконнекта (Экспоненциальная задержка - Пункт 3.2)
        this.reconnectAttempts = 0;
        this.baseDelay = 1000;       // Начальная задержка 1 сек
        this.maxDelay = 30000;       // Максимум 30 сек
        this.intentionalClose = false;
    }

    // Вычисление задержки: 1s, 2s, 4s, 8s, 16s, 30s...
    get _reconnectDelay() {
        return Math.min(
            this.baseDelay * Math.pow(2, this.reconnectAttempts),
            this.maxDelay
        );
    }

    get _wsUrl() {
        const url = this.token
            ? `${this.baseUrl}?token=${this.token}`
            : this.baseUrl;
        return url;
    }

    // Подключение к серверу
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
            this._emit('system', {
                type: 'disconnected',
                message: `Соединение потеряно (код ${e.code})`
            });
            this._scheduleReconnect();
        };

        this.ws.onerror = () => {
            this._emit('system', { type: 'error', message: 'Ошибка WebSocket' });
        };
    }

    // Планирование переподключения с экспоненциальной задержкой
    _scheduleReconnect() {
        const delay = this._reconnectDelay;
        this.reconnectAttempts++;

        this._emit('system', {
            type: 'reconnecting',
            message: `Переподключение через ${Math.round(delay / 1000)}с (попытка ${this.reconnectAttempts})`
        });

        setTimeout(() => {
            if (!this.intentionalClose) this.connect();
        }, delay);
    }

    // Отправка события на сервер
    send(event, data = {}) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.warn('[ChatClient] Соединение не готово');
            return false;
        }
        this.ws.send(JSON.stringify({ event, data }));
        return true;
    }

    // Подписка на событие
    on(event, callback) {
        if (!this.listeners[event]) this.listeners[event] = [];
        this.listeners[event].push(callback);
        return this; // Для цепочки вызовов: client.on(...).on(...)
    }

    // Вызов подписчиков события
    _emit(event, data) {
        (this.listeners[event] || []).forEach(cb => {
            try { cb(data); }
            catch (e) { console.error(`[ChatClient] Ошибка в обработчике '${event}':`, e); }
        });
    }

    // Намеренное отключение (без реконнекта)
    disconnect() {
        this.intentionalClose = true;
        if (this.ws) this.ws.close(1000, 'Пользователь вышел');
    }
}