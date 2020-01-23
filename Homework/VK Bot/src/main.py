# -*- coding: utf-8 -*-
import random
import argparse
import traceback

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.upload import VkUpload

import numpy as np
from skimage import io
from skimage.io import imread
from skimage import img_as_float
from sklearn.cluster import KMeans

# Эхо бот
# https://github.com/python273/vk_api
# Документация по python vk api с примерами
# https://vk.com/dev/manuals
# Общая документация по vk api


VK_TOKEN = 'your_sweet_and_tender_token'
GROUP_ID = 123456789
# Напишите сюда свой токен и id группы.


def parse_args():
    parser = argparse.ArgumentParser()  # Для параметров
    parser.add_argument('--vk_token', type=str, default=VK_TOKEN)
    parser.add_argument('--vk_group_id', type=int, default=GROUP_ID)
    return parser.parse_args()


def parse_text(text):
    if (text.find('bot') == 0 and text.find('clusterize') > 0):
        return 1
    return 0

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
                answer_text = "Cannot understard the meaning of your message, human. Use 'bot  help' if necessary"
                # изучим текст сообщения
                action = parse_text(text)
                if (action):
                    answer_text = 'Start to clasterize your image...'
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
                answer.update({'message': answer_text})
                vk_session.method('messages.send', answer)  # Отправляет сообщение
                # https://vk.com/dev/messages.send документация
                # Там еще есть очень много всего. Например, вместо peer_id можно оправлять user_id.
                print(answer)
                print()

            attachments = message['attachments']  # Вложенные файлы(это и изображения и музыка и видео и т.д)
            print(type(attachments))  # Так как их может быть несколько это список
            print(attachments)
            print()

            if len(attachments) > 0:
                if (action and attachments[0]['type'] == 'photo'):
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
                    img = io.imread(best_photo_url) #skimage умеет получать изображения по url
                    img_float = img_as_float(img)
                    # work with image
                    num_of_colors = 8 # количество цветов в ответном изображении
                    img_height = best_photo['height']
                    img_width = best_photo['width']
                    img_square = img_height * img_width
                    img_reshaped = np.ravel(img_float).reshape(img_square, 3)
                    kmeans = KMeans(random_state=0).fit(img_reshaped)
                    labels = kmeans.cluster_centers_.reshape(1,num_of_colors,3)
                    range1 = np.arange(num_of_colors)
                    img_final = img_reshaped.copy()
                    for i in range1:
                        img_final[kmeans.labels_ == i] = labels[0][i]
                    img_final = np.ravel(img_final).reshape(img_height,img_width,3)
                    #end working with image
                    io.imsave("test.png", img_final)  # сохраним изображение как test.png

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
                    # Можно отвечать и с текстом. 
                    # Но обязательно в сообщении должен быть или текст или вложение
                    print(answer_with_img)
                    print()
                elif(action):
                    answer_text("But wait, you don't send me image to clusterize. You should attach image to 'bot clusterize' command")
                  # Ответим пользователю
                    answer = {
                        'peer_id': peer_id,
                        'random_id': random.randint(0, 100000),
                    }
                    # Добавим текст к ответу
                    answer.update({'message': answer_text})
                    vk_session.method('messages.send', answer)  # Отправляет сообщение
                    print(answer)
                    print()
            elif(action):
                  answer_text("But wait, you don't send me image to clusterize. You should attach image to 'bot clusterize' command")
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
                  answer.update({'message': answer_text})
                  vk_session.method('messages.send', answer)  # Отправляет сообщение
                    # https://vk.com/dev/messages.send документация
                    # Там еще есть очень много всего. Например, вместо peer_id можно оправлять user_id.
                  print(answer)
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
