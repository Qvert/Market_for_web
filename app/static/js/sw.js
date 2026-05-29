/**
 * Service Worker для Push-уведомлений.
 * Работает в фоне, независимо от вкладки браузера.
 * Файл ОБЯЗАТЕЛЬНО должен лежать в корне статики: /static/js/sw.js
 */

const CACHE_NAME = 'market-notifications-v1';

// Установка Service Worker
self.addEventListener('install', (event) => {
    console.log('[SW] Установлен');
    self.skipWaiting(); // Активируем немедленно
});

self.addEventListener('activate', (event) => {
    console.log('[SW] Активирован');
    event.waitUntil(clients.claim()); // Берём управление над всеми вкладками
});

/**
 * Слушаем сообщения от основного потока (из notifications.js).
 * Когда приходит уведомление через WebSocket, основной поток
 * передаёт его сюда, а SW показывает системное уведомление.
 */
self.addEventListener('message', (event) => {
    const { type, notification } = event.data;

    if (type === 'SHOW_NOTIFICATION') {
        // Показываем системное Push-уведомление (Нативное, от ОС)
        event.waitUntil(
            self.registration.showNotification(notification.title, {
                body:    notification.body,
                icon:    notification.icon || '/static/img/logo.png',
                badge:   '/static/img/badge.png',
                tag:     notification.id || 'market-notification',
                data:    { url: notification.url || '/' },
                actions: [
                    { action: 'open',    title: 'Открыть' },
                    { action: 'dismiss', title: 'Закрыть' },
                ],
                vibrate:   [200, 100, 200], // Вибрация на мобильных
                renotify:  true,
            })
        );
    }
});

// Клик по системному уведомлению -> открываем нужную страницу
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    const url = event.notification.data?.url || '/';

    if (event.action === 'dismiss') return;

    // Открываем или фокусируемся на нужной вкладке
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // Ищем уже открытую вкладку с нашим сайтом
                for (const client of clientList) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        client.navigate(url);
                        return client.focus();
                    }
                }
                // Если вкладки нет — открываем новую
                if (clients.openWindow) {
                    return clients.openWindow(url);
                }
            })
    );
});