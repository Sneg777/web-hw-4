# Docker-команда FROM вказує базовий образ контейнера
# Наш базовий образ - це Linux з попередньо встановленим python
FROM python:3.12-slim

# Встановимо змінну середовища
ENV APP_HOME=/app

# Встановимо робочу директорію всередині контейнера
WORKDIR $APP_HOME

# Встановимо залежності всередині контейнера
COPY pyproject.toml poetry.lock $APP_HOME/

RUN pip install --upgrade poetry
RUN poetry install --no-dev

# Скопіюємо інші файли в робочу директорію контейнера
COPY . .

# Позначимо порт, де працює застосунок всередині контейнера
EXPOSE 3000

# Запустимо наш застосунок всередині контейнера
CMD ["python", "main.py"]
