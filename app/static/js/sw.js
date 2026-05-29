
const CACHE_NAME = 'market-push-v1';

// 1. Установка и активация
self.addEventListener('install', (event) => {
    console.log('[SW] Установлен');
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('[SW] Активирован и готов к работе');
    event.waitUntil(clients.claim());
});

/**
 * 2. Обработка входящих сообщений.
 * Вызывается, когда NotificationManager (из основного окна)
 * отправляет данные через postMessage.
 */
self.addEventListener('message', (event) => {
    const data = event.data;

    if (data.type === 'SHOW_NOTIFICATION') {
        const { notification } = data;

        const options = {
            body: notification.body || '',
            icon: notification.icon || '/static/img/logo.png', // Логотип сайта
            badge: '/static/img/badge.png',                  // Иконка в статус-баре (для Android)
            tag: notification.id || 'market-push-id',        // Группировка уведомлений
            data: {
                url: notification.url || '/'                 // Ссылка для перехода
            },
            vibrate: [200, 100, 200],                        // Вибрация
            requireInteraction: true,                        // Не закрывать автоматически быстро
            actions: [
                { action: 'open', title: 'Посмотреть' },
                { action: 'close', title: 'Закрыть' }
            ]
        };

        event.waitUntil(
            self.registration.showNotification(notification.title, options)
        );
    }
});

/**
 * 3. Логика клика по уведомлению.
 * Если пользователь нажал на уведомление — открываем вкладку или переходим по URL.
 */
self.addEventListener('notificationclick', (event) => {
    const notification = event.notification;
    const action = event.action;

    // Закрываем уведомление сразу после клика
    notification.close();

    if (action === 'close') return;

    const targetUrl = notification.data.url;

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((windowClients) => {
                // Если есть открытая вкладка нашего сайта — фокусируемся на ней и переходим
                for (let i = 0; i < windowClients.length; i++) {
                    const client = windowClients[i];
                    if (client.url.includes(self.location.origin) && 'navigate' in client) {
                        client.navigate(targetUrl);
                        return client.focus();
                    }
                }
                // Если вкладок нет — открываем новую
                if (clients.openWindow) {
                    return clients.openWindow(targetUrl);
                }
            })
    );
});

/**
 * 4. Обработка нативного Push (на будущее).
 * Если ты решишь использовать Firebase Cloud Messaging или ntfy через Web Push API.
 */
self.addEventListener('push', (event) => {
    if (!event.data) return;

    try {
        const data = event.data.json();
        const title = data.title || 'Новое уведомление';
        const options = {
            body: data.message || data.body,
            icon: '/static/img/logo.png',
            data: { url: data.click || data.url || '/' }
        };

        event.waitUntil(
            self.registration.showNotification(title, options)
        );
    } catch (e) {
        console.error('[SW] Ошибка обработки Push-события:', e);
    }
});