# Сайт Yatube - социальная сеть блогеров
## Описание проекта
Сайт Yatube представляет собой социальную сеть, где каждый зарегистрированный пользователь может создавать посты, оставлять к ним комментарии, подписывать на других авторов, создавать группы для постов одной тематики.


## Модели

* **Сообщение**
    `text` * - Текст поста
    `pub_date` * - Дата публикации поста
    `author` * - Автор поста
    `group` * - Сообщество поста
    `image` * - Картинка поста
* **Группа**
    `title` * - Название группы
    `slug` * - Адрес группы
    `description` * - Описание группы
* **Комментарий**
    `post` * - Пост, к которому написан комментарий
    `author` * - Автор комментария
    `text` * - Текст комментария
    `created` * - Дата создания комментария
* **Подписывайтесь**
    `user` * - Подписки пользователя
    `author` * - Авторизованный пользователь


## View-функции

`index` * - передаёт в шаблон `posts/index.html` объекты модели `Post`, отсортированные по дате публикации
`group_posts` * - передаёт в шаблон `posts/group_list.html` посты, отфильтрованные по группам
`profile` * - передаёт в шаблон `posts/profile.html` информацию о пользователе
`post_detail` * - передаёт в шаблон `posts/post_detail.html` детальную информацию о посте
`post_create` * - передаёт в шаблон `posts/create_post.html` форму для создания поста
`post_edit` * - передаёт в шаблон `posts/create_post.html` форму для редактирования поста
`add_comment` * - передаёт в шаблон `posts/post_detail.html` форму для добавления комментария к посту
`follow_index` * - передаёт в шаблон `posts/follow.html` посты автора, на которого подписан пользователь
`profile_follow` * - позволяет подписываться на определенного пользователя
`profile_unfollow` * - позволяет отписываться от определенного пользователя





## Запуск проекта в dev-режиме
- Клонируем репозиторию на компьютер:
```bash
1) git clone https://github.com/SergeiTregubov/hw05_final.git
2) cd hw05_final
```
- Cоздать и активировать виртуальное окружение:
```bash
python -m venv venv # Windows
```
```bash
python3 -m venv venv # Linux
```
```bash
source venv/Scripts/activate # Windows
```
```
source venv/bin/activate # Linux
```
- Установить зависимости проекта:
```
pip install -r requirements.txt
```
- Перейти в директорию:
```
cd hw05_final/yatube/
```
- Создать и выполнить миграции:
```bash
python manage.py makemigrations
```
```
python manage.py migrate
```
- Запуск сервера локально:
```bash
python manage.py runserver
```
- Создаём суперпользователя(admin/root):
```bash
python manage.py createsuperuser
```
