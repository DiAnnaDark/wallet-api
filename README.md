wallet-api

REST API для пополнения кошельков, списания денег и получения баланса

Python 3.12, FastAPI, PostgreSQL, asyncpg

Запуск

Создать .env по примеру .env.example и указать пароль PostgreSQL

docker compose up --build -d

Миграции выполняются автоматически при запуске

Документация API доступна по адресу http://localhost:8001/docs

Запросы

POST /api/v1/wallets/{wallet_uuid}/operation

{"operation_type": "DEPOSIT", "amount": 1000}

DEPOSIT пополняет баланс, WITHDRAW списывает деньги

При первом пополнении кошелёк создаётся автоматически

GET /api/v1/wallets/{wallet_uuid}

Возвращает текущий баланс

Несуществующий кошелёк - 404

Недостаточно средств - 409

Некорректные данные - 422

Изменение баланса выполняется атомарным SQL-запросом для корректной работы параллельных запросов

Тесты

При запущенном приложении выполнить

python -m pip install -r requirements.txt

python -m pytest tests/ -v

Остановка

docker compose down

Данные сохраняются в Docker volume