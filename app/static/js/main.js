// Ждем загрузки DOM
document.addEventListener('DOMContentLoaded', () => {
    updateCartCounter(); // Обновляем счетчик при загрузке страницы
    setupEventListeners();
});

function setupEventListeners() {
    // 1. Динамическое добавление в корзину (3.1)
    const addToCartButtons = document.querySelectorAll('.add-to-cart-btn');
    addToCartButtons.forEach(button => {
        button.addEventListener('click', async (e) => {
            const productId = e.target.dataset.productId;
            await addToCart(productId);
        });
    });

    // 2. Проверка email при регистрации (3.4)
    const emailInput = document.getElementById('register-email');
    if (emailInput) {
        emailInput.addEventListener('blur', async () => {
            const email = emailInput.value;
            if (email) await checkEmailUniqueness(email);
        });
    }
}

// --- Функции для работы с Корзиной ---

// Добавление товара
async function addToCart(productId) {
    try {
        const response = await fetch('/api/cart/items', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: productId, quantity: 1 })
        });

        if (response.ok) {
            const data = await response.json();
            alert('Товар добавлен в корзину!');
            updateCartCounter();
        } else {
            const error = await response.json();
            alert(`Ошибка: ${error.detail || 'Не удалось добавить товар'}`);
        }
    } catch (err) {
        console.error('Ошибка сети:', err);
    }
}

// Изменение количества (3.2)
async function updateQuantity(productId, newQuantity) {
    if (newQuantity < 1) return;

    try {
        const response = await fetch(`/api/cart/items/${productId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quantity: newQuantity })
        });

        if (response.ok) {
            // Перезагружаем часть страницы или просто обновляем итоговую сумму
            location.reload(); // Для простоты в SSR, либо динамически:
            // updateTotals();
        }
    } catch (err) {
        console.error('Ошибка обновления:', err);
    }
}

// Удаление товара (3.2)
async function removeItem(productId) {
    if (!confirm('Удалить товар из корзины?')) return;

    try {
        const response = await fetch(`/api/cart/items/${productId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            location.reload();
        }
    } catch (err) {
        console.error('Ошибка удаления:', err);
    }
}

// Обновление счетчика в шапке
async function updateCartCounter() {
    const counter = document.getElementById('cart-count');
    if (!counter) return;

    try {
        const response = await fetch('/api/cart/count');
        const data = await response.json();
        counter.textContent = data.count;
    } catch (err) {
        console.log('Корзина пуста или не авторизован');
    }
}

// --- Быстрый просмотр (3.3) ---
async function quickView(productId) {
    try {
        const response = await fetch(`/api/products/${productId}`);
        const product = await response.json();

        // Предполагается, что у вас есть модальное окно с ID 'quickViewModal'
        const modal = document.getElementById('quickViewModal');
        modal.querySelector('.modal-title').textContent = product.name;
        modal.querySelector('.modal-body img').src = product.image_url;
        modal.querySelector('.modal-description').textContent = product.description;

        // Показать модалку (зависит от вашего CSS/фреймворка)
        modal.style.display = 'block';
    } catch (err) {
        console.error('Ошибка загрузки данных товара:', err);
    }
}

// --- Проверка Email (3.4) ---
async function checkEmailUniqueness(email) {
    const feedback = document.getElementById('email-feedback');
    try {
        const response = await fetch(`/api/auth/check-email?email=${encodeURIComponent(email)}`);
        const data = await response.json();

        if (data.exists) {
            feedback.textContent = 'Этот email уже занят';
            feedback.style.color = 'red';
        } else {
            feedback.textContent = 'Email свободен';
            feedback.style.color = 'green';
        }
    } catch (err) {
        console.error('Ошибка проверки email');
    }
}