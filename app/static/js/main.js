document.addEventListener('DOMContentLoaded', () => {
    // 1. Инициализация систем
    updateCartCounter();
    setupEventListeners();
    initNotifications();

    // 2. Первичная загрузка товаров, если мы на главной (где есть контейнер)
    const productContainer = document.getElementById('product-list');
    if (productContainer) {
        loadProducts();
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

            // --- ВОТ ТУТ ЛОГИКА ОДНОКРАТНОГО ПОКАЗА ---
            if (!sessionStorage.getItem('notified_connected')) {
                // Вызываем показ тоста вручную через созданный менеджер
                window.notificationManager._showToast({
                    title: "Уведомления подключены",
                    body: "Вы будете получать сообщения о событиях системы",
                    type: "success",
                    ts: new Date().toISOString()
                });

                // Ставим метку, что мы уже поприветствовали пользователя
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

    container.innerHTML = '<div class="loader">Загрузка товаров...</div>';

    try {
        const url = categoryId ? `/api/products/?category_id=${categoryId}` : '/api/products/';
        const response = await fetch(url);
        const products = await response.json();

        renderProducts(products);
    } catch (err) {
        console.error("Ошибка загрузки:", err);
        container.innerHTML = '<p>Ошибка загрузки товаров.</p>';
    }
}

function renderProducts(products) {
    const container = document.getElementById('product-list');
    container.innerHTML = '';

    if (products.length === 0) {
        container.innerHTML = '<p>Товары не найдены.</p>';
        return;
    }

    products.forEach(product => {
        const card = document.createElement('div');
        card.className = 'product-card';
        card.innerHTML = `
            <div class="product-info">
                <h3>${product.name}</h3>
                <p>${product.description}</p>
                <div class="product-footer">
                    <span class="price">${product.price} руб.</span>
                    <button class="add-to-cart-btn btn-sm" data-product-id="${product.id}">
                        В корзину
                    </button>
                </div>
            </div>
        `;
        container.appendChild(card);
    });

    // Важно: Привязываем события сразу после отрисовки
    bindAddToCartEvents();
}

// Функция поиска и привязки всех кнопок "В корзину" на странице
function bindAddToCartEvents() {
    const btns = document.querySelectorAll('.add-to-cart-btn');
    btns.forEach(btn => {
        // Убираем старый обработчик, чтобы не было дублей, и ставим новый
        btn.onclick = async (e) => {
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
            catButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            loadProducts(id);
        });
    });

    // Привязываем кнопки корзины, которые уже могут быть в HTML
    bindAddToCartEvents();

    // Формы (регистрация/вход) - код без изменений
    const regForm = document.getElementById('register-form');
    if (regForm) {
        regForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('reg-name').value;
            const email = document.getElementById('reg-email').value;
            const password = document.getElementById('reg-password').value;
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password })
            });
            if (response.ok) window.location.href = '/auth/login';
        });
    }

    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('login-email').value;
            const password = document.getElementById('login-password').value;
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            if (response.ok) window.location.href = '/';
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
                product_id: Number(productId), // Явно преобразуем в число
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
            }
        } else {
            const err = await response.json();
            alert(err.detail || "Ошибка добавления");
        }
    } catch (err) {
        console.error("Ошибка корзины:", err);
    }
}

async function updateCartCounter() {
    const counter = document.getElementById('cart-count');
    if (!counter) return;
    try {
        const response = await fetch('/api/cart/count');
        const data = await response.json();
        counter.textContent = data.count;
    } catch (err) { console.log('Корзина пуста'); }
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
            // Мы не делаем alert! Уведомление прилетит само через Push/Socket
            console.log("Заказ оформлен на сервере");

            // Если мы на странице корзины — очищаем таблицу или редиректим
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