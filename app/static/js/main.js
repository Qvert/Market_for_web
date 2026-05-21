// Ждем загрузки DOM
document.addEventListener('DOMContentLoaded', () => {
    updateCartCounter();
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

    // 2. Проверка email при регистрации (3.4) - ИСПРАВЛЕН ID на 'reg-email'
    const emailInput = document.getElementById('reg-email');
    if (emailInput) {
        emailInput.addEventListener('blur', async () => {
            const email = emailInput.value;
            if (email) await checkEmailUniqueness(email);
        });
    }

    // 3. Обработка формы регистрации - ТЕПЕРЬ ВНУТРИ setupEventListeners
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            console.log("Попытка регистрации...");

            const name = document.getElementById('reg-name').value;
            const email = document.getElementById('reg-email').value;
            const password = document.getElementById('reg-password').value;
            const errorElement = document.getElementById('register-error');

            try {
                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, email, password })
                });

                const result = await response.json();

                if (response.ok) {
                    alert('Регистрация успешна!');
                    // Проверьте путь в views.py. Если страница логина по адресу /login, то:
                    window.location.href = '/auth/login';
                } else {
                    if (errorElement) {
                        errorElement.textContent = result.detail || 'Ошибка регистрации';
                        errorElement.style.display = 'block';
                    } else {
                        alert(result.detail || 'Ошибка регистрации');
                    }
                }
            } catch (error) {
                console.error('Ошибка запроса:', error);
                alert('Не удалось связаться с сервером');
            }
        });
    }
    // Обработка формы входа
const loginForm = document.getElementById('login-form');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // Стоп перезагрузка

        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        const errorElement = document.getElementById('login-error');

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const result = await response.json();

            if (response.ok) {
                // Если вход успешен, перенаправляем на главную
                window.location.href = '/';
            } else {
                // Выводим ошибку (например, "Неверный пароль")
                errorElement.textContent = result.detail || 'Ошибка входа';
                errorElement.style.display = 'block';
            }
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Не удалось связаться с сервером');
        }
    });
}
}

// --- Функции-помощники ---

async function addToCart(productId) {
    try {
        const response = await fetch('/api/cart/items', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: productId, quantity: 1 })
        });
        if (response.ok) {
            alert('Товар добавлен!');
            updateCartCounter();
        }
    } catch (err) { console.error(err); }
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

async function checkEmailUniqueness(email) {
    const feedback = document.getElementById('email-feedback');
    if (!feedback) return;
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
    } catch (err) { console.error('Ошибка проверки email'); }
}
async function updateQuantity(productId, newQuantity) {
    // Если пытаемся сделать меньше 1, ничего не делаем
    if (newQuantity < 1) return;

    try {
        const response = await fetch(`/api/cart/items/${productId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ quantity: newQuantity })
        });

        if (response.ok) {
            // Самый простой способ обновить итоговую сумму и список в SSR — перезагрузить страницу
            location.reload();
        } else {
            const error = await response.json();
            alert('Ошибка при обновлении: ' + (error.detail || 'Неизвестная ошибка'));
        }
    } catch (err) {
        console.error('Ошибка запроса:', err);
    }
}
async function removeItem(productId) {
    if (!confirm('Вы уверены, что хотите удалить этот товар из корзины?')) return;

    try {
        const response = await fetch(`/api/cart/items/${productId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            // Перезагружаем страницу, чтобы увидеть обновленную корзину
            location.reload();
        } else {
            const error = await response.json();
            alert('Ошибка при удалении: ' + (error.detail || 'Неизвестная ошибка'));
        }
    } catch (err) {
        console.error('Ошибка удаления:', err);
    }
}