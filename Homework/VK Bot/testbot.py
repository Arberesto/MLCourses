# -*- coding: utf-8 -*-
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.upload import VkUpload

import random
import argparse
import traceback

from skimage import io

# Эхо бот
# https://github.com/python273/vk_api
# Документация по python vk api с примерами
# https://vk.com/dev/manuals
# Общая документация по vk api


VK_TOKEN = '65c856a6743be09f0f89dce9d984872a7335059ded5827c7db65c3d65cb3c5a6f97acf93eb6c99f1707ed'
GROUP_ID = 191130961
# Напишите сюда свой токен и id группы.


def parse_args():
    parser = argparse.ArgumentParser()  # Для параметров
    parser.add_argument('--vk_token', type=str, default=VK_TOKEN)
    parser.add_argument('--vk_group_id', type=int, default=GROUP_ID)
    return parser.parse_args()


def main():
    params = parse_args()

    vk_session = vk_api.VkApi(token=params.vk_token)
    uploader = VkUpload(vk_session)  # Понадобится для загрузки своих изображений в вк
    long_poll = VkBotLongPoll(vk_session, params.vk_group_id)

    for event in long_poll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            print(type(event.obj))
            print(event.obj)  # Тут хранится все инфорация о сообщении
            print()

            message = event.obj.message
            peer_id = message['peer_id']  # ID пользователя куда отсылать ответ
            from_id = message['from_id']  # ID пользователя который прислал сообщение
            text = message['text']  # Текст сообщения

            if len(text) > 0:
                # Ответим пользователю
                answer = {
                    'peer_id': peer_id,
                    # peer_id - ID кому отвечаем. Подробнее смотрите в документации. Нам сейчас и этого достаточно.
                    'random_id': random.randint(0, 100000),
                    # random_id - уникальный (в привязке к API_ID и ID отправителя) идентификатор,
                    # предназначенный для предотвращения повторной отправки одинакового сообщения.
                    # Сохраняется вместе с сообщением и доступен в истории сообщений.
                    # Заданный random_id используется для проверки уникальности за всю историю сообщений,
                    # поэтому используйте большой диапазон (до int64).
                }
                # Добавим текст к ответу
                answer.update({'message': text})
                vk_session.method('messages.send', answer)  # Отправляет сообщение
                # https://vk.com/dev/messages.send документация
                # Там еще есть очень много всего. Например, вместо peer_id можно оправлять user_id.
                print(answer)
                print()

            attachments = message['attachments']  # Вложенные файлы(это и изображения и музыка и видео и т.д)
            print(type(attachments))  # Так как их может быть несколько это список
            print(attachments)
            print()

            if len(attachments) > 0 and attachments[0]['type'] == 'photo':
                photo = attachments[0]['photo']
                print(type(photo))
                print(photo)
                print()
                # Как вы видете там очень много изображений разного размера.
                # Возьмем изображение в самом лучшем качества.
                photos = sorted(photo['sizes'], key=lambda a: a['height'], reverse=True)
                # Отсортируем по размеру
                best_photo = photos[0]
                best_photo_url = best_photo['url']
                img = io.imread(best_photo_url)  # skimage умеет получать изображения по url
                io.imsave("test.png", img)  # сохраним изображение как test.png

                uploaded_photos = uploader.photo_messages("./test.png")
                # Можно загрузить несколько изображений сразу.
                # Выглядит так же как и attachment которые мы получаем в сообщении
                uploaded_photo = uploaded_photos[0]
                # Но сейчас у нас только одно.

                answer_with_img = {
                    'peer_id': peer_id,
                    'random_id': random.randint(0, 100000),
                }
                photo_attachment = f'photo{uploaded_photo["owner_id"]}_{uploaded_photo["id"]}'
                # <type><owner_id>_<media_id> Так должны выглядить вложенные изображения.
                # Например photo100172_166443618
                # Подробнее в https://vk.com/dev/messages.send

                # Добавим изображение к ответу
                answer_with_img.update({'attachment': photo_attachment})
                vk_session.method('messages.send', answer_with_img)
                # Можно отвечать и с текстом. Но обязательно в сообщении должен быть или текст или вложение
                print(answer_with_img)
                print()


# Это всего лишь пример, а не идеальный код.
# Как вы видите vk_api не очень удобное.
# И многие его части можно завернуть в классы и методы для удобства.

if __name__ == '__main__':
    while True:
        try:  # Чтоб не падало
            print("(RE)START")
            main()
        except Exception as err:
            full_stack_trace = traceback.format_exc()
            # Возвращяет всю ошибку. Иначе написало бы только последную строку
            print("BLIN {}".format(full_stack_trace))
