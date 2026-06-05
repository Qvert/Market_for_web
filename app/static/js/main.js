document.addEventListener('DOMContentLoaded', () => {
    // 1. Инициализация систем
    updateCartCounter();
    setupEventListeners();
    initNotifications();

    // 2. Первичная загрузка товаров только на главной странице
    // На странице catalog товары уже отрендерены сервером
    const productContainer = document.getElementById('product-list');
    if (productContainer && window.location.pathname === '/') {
        loadProducts();
    }

    // 3. Если мы на странице catalog - привязываем события к существующим кнопкам
    if (productContainer && window.location.pathname === '/catalog') {
        bindAddToCartEvents();
    }
});

// --- СИСТЕМА УВЕДОМЛЕНИЙ ---
async function initNotifications() {
    try {
        const response = await fetch('/api/auth/me');
        if (response.ok) {
            const user = await response.json();
            const userId = user.email;

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/api/notify/subscribe`;

            const manager = new NotificationManager(wsUrl, userId, userId);
            await manager.init();
            window.notificationManager = manager;

            if (!sessionStorage.getItem('notified_connected')) {
                window.notificationManager._showToast({
                    title: "Уведомления подключены",
                    body: "Вы будете получать сообщения о событиях системы",
                    type: "success",
                    ts: new Date().toISOString()
                });
                sessionStorage.setItem('notified_connected', 'true');
                console.log('[Notifications] Приветствие показано в первый раз');
            } else {
                console.log('[Notifications] Приветствие уже было в этой сессии, пропускаем');
            }
        }
    } catch (err) {
        console.log('[Notifications] Вход не выполнен, уведомления не инициализированы');
    }
}

// --- КАТАЛОГ ТОВАРОВ (AJAX) ---
async function loadProducts(categoryId = '') {
    const container = document.getElementById('product-list');
    if (!container) return;

    container.innerHTML = '<div class="loader" style="text-align: center; padding: 2rem; font-size: 1.2rem;">Загрузка товаров...</div>';

    try {
        let url = '/api/catalog/products';
        if (categoryId) {
            url = `/api/catalog/products?category_id=${categoryId}`;
        }

        console.log('Загрузка товаров:', url);

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const products = await response.json();
        console.log('Получено товаров:', products.length);

        renderProducts(products);
    } catch (err) {
        console.error("Ошибка загрузки:", err);
        container.innerHTML = '<p style="text-align: center; padding: 2rem; color: #dc3545;">Ошибка загрузки товаров. Попробуйте обновить страницу.</p>';
    }
}

function renderProducts(products) {
    const container = document.getElementById('product-list');
    container.innerHTML = '';

    if (products.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 2rem; color: #666;">Товары не найдены в данной категории.</p>';
        return;
    }

    products.forEach(product => {
        const card = document.createElement('div');
        card.className = 'product-card';
        card.style.cssText = 'border: 1px solid #ccc; padding: 20px; width: 250px; border-radius: 8px; text-align: center;';
        card.innerHTML = `
            <h3><a href="/product/${product.id}" style="text-decoration: none; color: #333;">${product.name}</a></h3>
            <h2 style="color: #d9534f;">${product.price} руб.</h2>

            <button onclick="quickView('${product.id}')" style="margin-bottom: 10px; cursor: pointer; padding: 8px 15px; background: #17a2b8; color: white; border: none; border-radius: 4px; width: 100%;">
                Быстрый просмотр
            </button>

            <button class="add-to-cart-btn" data-product-id="${product.id}"
                    style="padding: 10px; background: #28a745; color: white; border: none; cursor: pointer; border-radius: 4px; width: 100%;">
                Добавить в корзину
            </button>
        `;
        container.appendChild(card);
    });

    // Привязываем события сразу после отрисовки
    bindAddToCartEvents();
}

// --- БЫСТРЫЙ ПРОСМОТР ---
async function quickView(productId) {
    try {
        const response = await fetch(`/api/catalog/product/${productId}`);
        if (!response.ok) {
            throw new Error('Товар не найден');
        }

        const product = await response.json();

        // Заполняем модальное окно
        document.querySelector('.modal-title').textContent = product.name;
        document.querySelector('.modal-description').textContent = product.description;
        document.querySelector('.modal-price').textContent = `${product.price} руб.`;

        // Показываем модальное окно и затемнение
        document.getElementById('quickViewModal').style.display = 'block';
        document.getElementById('modalOverlay').style.display = 'block';

    } catch (err) {
        console.error('Ошибка быстрого просмотра:', err);
        alert('Не удалось загрузить информацию о товаре');
    }
}

// Функция поиска и привязки всех кнопок "В корзину" на странице
function bindAddToCartEvents() {
    const btns = document.querySelectorAll('.add-to-cart-btn');
    btns.forEach(btn => {
        btn.onclick = async (e) => {
            e.preventDefault();
            const id = e.target.getAttribute('data-product-id');
            await addToCart(id);
        };
    });
}

// --- ОБРАБОТЧИКИ СОБЫТИЙ ---
function setupEventListeners() {
    // Категории
    const catButtons = document.querySelectorAll('.cat-btn');
    catButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const id = btn.getAttribute('data-id');

            // Убираем активный класс у всех кнопок
            catButtons.forEach(b => {
                b.style.background = 'white';
                b.style.color = '#007bff';
                b.classList.remove('active');
            });

            // Добавляем активный класс текущей кнопке
            btn.style.background = '#007bff';
            btn.style.color = 'white';
            btn.classList.add('active');

            console.log('Выбрана категория:', id || 'Все товары');

            // Загружаем товары по категории
            loadProducts(id);
        });
    });

    // Привязываем кнопки корзины, которые уже могут быть в HTML
    bindAddToCartEvents();

    // Форма регистрации
    const regForm = document.getElementById('register-form');
    if (regForm) {
        regForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('reg-name').value;
            const email = document.getElementById('reg-email').value;
            const password = document.getElementById('reg-password').value;

            try {
                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, email, password })
                });

                if (response.ok) {
                    window.location.href = '/auth/login';
                } else {
                    const error = await response.json();
                    alert(error.detail || 'Ошибка регистрации');
                }
            } catch (err) {
                console.error('Ошибка регистрации:', err);
                alert('Ошибка подключения к серверу');
            }
        });
    }

    // Форма входа
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('login-email').value;
            const password = document.getElementById('login-password').value;

            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                if (response.ok) {
                    window.location.href = '/';
                } else {
                    const error = await response.json();
                    alert(error.detail || 'Ошибка входа');
                }
            } catch (err) {
                console.error('Ошибка входа:', err);
                alert('Ошибка подключения к серверу');
            }
        });
    }
}

// --- КОРЗИНА ---
async function addToCart(productId) {
    if (!productId) return;

    try {
        const response = await fetch('/api/cart/items', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_id: Number(productId),
                quantity: 1
            })
        });

        if (response.ok) {
            updateCartCounter();
            if (window.notificationManager) {
                window.notificationManager._showToast({
                    title: "Корзина",
                    body: "Товар успешно добавлен",
                    type: "success",
                    ts: new Date().toISOString()
                });
            } else {
                alert('Товар добавлен в корзину');
            }
        } else {
            const err = await response.json();
            alert(err.detail || "Ошибка добавления");
        }
    } catch (err) {
        console.error("Ошибка корзины:", err);
        alert('Ошибка подключения к серверу');
    }
}

async function updateCartCounter() {
    const counter = document.getElementById('cart-count');
    if (!counter) return;
    try {
        const response = await fetch('/api/cart/count');
        const data = await response.json();
        counter.textContent = data.count;
    } catch (err) {
        console.log('Корзина пуста');
    }
}

// Функции для страницы корзины
async function removeItem(productId) {
    if (!confirm('Удалить товар?')) return;
    const response = await fetch(`/api/cart/items/${productId}`, { method: 'DELETE' });
    if (response.ok) {
        const row = document.getElementById(`row-${productId}`);
        if (row) row.remove();
        recalculateTotal();
        updateCartCounter();
    }
}

async function changeQuantity(productId, delta) {
    const qtyElement = document.getElementById(`qty-${productId}`);
    if (!qtyElement) return;
    let newQty = parseInt(qtyElement.textContent) + delta;
    if (newQty < 1) return;

    const response = await fetch(`/api/cart/items/${productId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quantity: newQty })
    });

    if (response.ok) {
        qtyElement.textContent = newQty;
        const row = qtyElement.closest('tr');
        const price = parseFloat(row.querySelector('.item-price').textContent);
        row.querySelector('.item-total').textContent = (price * newQty);
        recalculateTotal();
    }
}

function recalculateTotal() {
    let total = 0;
    document.querySelectorAll('.item-total').forEach(el => {
        total += parseFloat(el.textContent);
    });
    const totalEl = document.getElementById('total-price');
    if (totalEl) totalEl.textContent = total + " руб.";
}

async function placeOrder() {
    try {
        const response = await fetch('/api/cart/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (response.ok) {
            console.log("Заказ оформлен на сервере");
            if (window.location.pathname === '/cart') {
                setTimeout(() => window.location.href = '/', 2000);
            }
        }
    } catch (err) {
        console.error("Ошибка оформления:", err);
    }
}

const checkoutBtn = document.getElementById('checkout-btn');
if (checkoutBtn) {
    checkoutBtn.addEventListener('click', placeOrder);
}