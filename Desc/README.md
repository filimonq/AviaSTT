# 🛫 AviaSTT - Система транскрипции авиационных переговоров

![](https://github.com/filimonq/AviaSTT/blob/70fb69346c624c728327571f0f7fe9c03ef2f7c1/Desc/img.png)
---

## 🧩 Основные объекты продукта


| Объект           | Атрибуты                     | Связи                          |
|------------------|------------------------------|--------------------------------|
| Пользователь     | Роль, доступные функции  | Взаимодействует с аудиомодулем |
| Аудиовход        | Источник речи                     | Передает данные в обработчик   |
| Транскрипция     | Текст |   Выводится в приложение   |

### 🟩**Ключевые операции**
```mermaid
graph TD
  A[Запись аудио] --> C[Распознание речи]
  C --> D[Коррекция через ICAO]
  D --> E[Вывод текста]

  style A fill:#E0F2E9,stroke:#4CAF50,stroke-width:2px,color:#000000
  style C fill:#E0F2E9,stroke:#4CAF50,stroke-width:2px,color:#000000
  style D fill:#E0F2E9,stroke:#4CAF50,stroke-width:2px,color:#000000
  style E fill:#E0F2E9,stroke:#4CAF50,stroke-width:2px,color:#000000
```

---

## 📗 Ролевая модель

| Роль      | Функции                | Ограничения      |
| --------- | ---------------------- | ---------------- |
| Пилот     | Запись голоса          | Речь на английском языке                |
| Диспетчер | Получение транскрипции | Доступ в интернет |

---

## ✅ Требования

**Пользовательские:**
- Доступ в интернет(для диспетчера)

**Функциональные:**
- Запись аудио в реальном времени
- Интеграция с базой данных ICAO
- Распознавание фразеологии ICAO

---

## 🖼️ Прототипы интерфейса

![interface](https://github.com/filimonq/AviaSTT/blob/4b3f3466b9e5f8eabbd5763c89c8206e93f739f9/Desc/PNG/gui.png)

---

## ✳️ Перспективы расширения

1. Поддержка нескольких языков(терминологии ICAO)
2. Моментальная конвертация речи в текст
##  
##

[⬆ Наверх](#-aviaSTT---система-транскрипции-авиационных-переговоров)
