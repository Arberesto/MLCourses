# -*- coding: utf-8 -*-
import random
import argparse
import traceback

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.upload import VkUpload

import numpy as np
import pandas as pd
from time import time
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

original_name = 'bot'
original_human = 'human'

current_name = original_name
current_human = original_human

vk_session = None
repeat_time = 0

default_answer_text = "Cannot understard the meaning of your message, {1}. Use '{0}  help' if necessary".format(
    current_name, current_human)


def parse_args():
    parser = argparse.ArgumentParser()  # Для параметров
    parser.add_argument('--vk_token', type=str, default=VK_TOKEN)
    parser.add_argument('--vk_group_id', type=int, default=GROUP_ID)
    parser.add_argument('--bot_default_name', type=str, default=original_name)
    parser.add_argument('--human_default_name', type=str, default=original_human)
    return parser.parse_args()


def parse_text(text, bot_name=original_name):
    tokens = text.split(maxsplit=1)
    print("initial tokens:{0}; len - {1}".format(tokens, len(tokens)))
    if (tokens[0] == bot_name):
        tokens_result = []
        if (len(tokens) > 1):
            tokens_result = tokens[1].split()
        print("after_tokens:{0}; len - {1}".format(tokens_result, len(tokens_result)))
        return tokens_result, len(tokens_result)
    return "", -1


def answer_to(peer_id, answer_text=default_answer_text):
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

def num_of_image_colors(image):
    # image in shape (X,3), where X = height*width
    img_series = pd.DataFrame(np.around(image, decimals=5), columns=['red', 'green', 'blue'],
                              dtype=object)
    img_series['color'] = img_series['red'].map(str) + img_series['green'].map(str) + img_series[
        'blue'].map(str)
    # for example, 608874 colors in jpeg image,58859 in png image
    unique_colors = len(img_series['color'].unique())
    print("Unique colors in image: {0}\n".format(unique_colors))
    return unique_colors


def clusterize(message, uploader, num_of_colors=8):
    time_start = time()
    attachments = message['attachments']
    if (num_of_colors > 1):
        if len(attachments) > 0:
            if attachments[0]['type'] == 'photo':
                answer_text = 'Start to clasterize your image with {0} colors...'.format(num_of_colors)
                answer_to(message['peer_id'], answer_text)
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
                img_float = img_as_float(img)
                # work with image
                img_height = best_photo['height']
                img_width = best_photo['width']
                img_square = img_height * img_width
                img_reshaped = np.ravel(img_float).reshape(img_square, 3)
                unique_colors = num_of_image_colors(img_reshaped)
                if num_of_colors <= unique_colors:
                    kmeans = KMeans(n_clusters=num_of_colors, random_state=0, n_jobs=2).fit(img_reshaped)
                    print(
                        "cluster centers: {0}; shape = {1} ".format(kmeans.cluster_centers_,
                                                                    kmeans.cluster_centers_.shape))
                    labels = kmeans.cluster_centers_.reshape(1, num_of_colors, 3)
                    range1 = np.arange(num_of_colors)
                    img_final = img_reshaped.copy()
                    for i in range1:
                        img_final[kmeans.labels_ == i] = labels[0][i]
                    img_final = np.ravel(img_final).reshape(img_height, img_width, 3)
                    # end working with image
                    io.imsave("test.jpg", img_final)  # сохраним изображение как test.png

                    uploaded_photos = uploader.photo_messages("./test.jpg")
                    # Можно загрузить несколько изображений сразу.
                    # Выглядит так же как и attachment которые мы получаем в сообщении
                    uploaded_photo = uploaded_photos[0]
                    # Но сейчас у нас только одно.

                    answer_with_img = {
                        'peer_id': message['peer_id'],
                        'random_id': random.randint(0, 100000),
                    }
                    photo_attachment = f'photo{uploaded_photo["owner_id"]}_{uploaded_photo["id"]}'
                    # <type><owner_id>_<media_id> Так должны выглядить вложенные изображения.
                    # Например photo100172_166443618
                    # Подробнее в https://vk.com/dev/messages.send

                    # Добавим изображение к ответу
                    time_used = time() - time_start
                    answer_text = 'Image clusterized successfully for {0} seconds'.format(time_used)
                    answer_with_img.update({'attachment': photo_attachment})
                    answer_with_img.update({'message': answer_text})
                    vk_session.method('messages.send', answer_with_img)
                else:
                    answer_text = "Error: try to clusterize with {0} colors," \
                                  " but image contain only {1} colors.".format(num_of_colors, unique_colors)
                    answer_to(message['peer_id'], answer_text)

            else:
                answer_text = "But wait, you don't send me image to clusterize. " \
                              "You should attach image to '{0} clusterize' command".format(original_name)
                answer_to(message['peer_id'], answer_text)
        else:
            answer_text = "Error: trying to clusterize with {0} colors, but minimum is 2 colors. ".format(num_of_colors)
            answer_to(message['peer_id'], answer_text)
        time_used = time() - time_start
        print("clusterize time - {0} sec".format(time_used))

def ask_what(message):
    answer_text = "What do you want, {0} ?If you don't know what to say, use '{1} help'?".format(current_human,
                                                                                                     current_name)
    answer_to(message['peer_id'], answer_text)

def get_help(message):
    help_message = "1. Type '{0} clusterize X' and attach image to message to get X-colored version of it.\n" \
                   "   If not defined, X = 8 and can't be less than 2 and greater than number of colors in image\n" \
                   "   Warning: using X>100 may cause bot to crash \n" \
                   "2. Type '{0} help' to get that message again\n" \
                   "3. If you just type '{0}', I get you advice. Be grateful, {1}".format(
        current_name, current_human)
    answer_text = 'Now you asking me for help? Okey then\n' + help_message
    answer_to(message['peer_id'], answer_text)

def main():
    params = parse_args()
    global vk_session
    vk_session = vk_api.VkApi(token=params.vk_token)
    uploader = VkUpload(vk_session)  # Понадобится для загрузки своих изображений в вк
    long_poll = VkBotLongPoll(vk_session, params.vk_group_id)
    global current_name
    current_name = params.bot_default_name
    global current_human
    current_human = params.human_default_name
    for event in long_poll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            print(type(event.obj))
            print(event.obj)  # Тут хранится все инфорация о сообщении
            print()
            message = event.obj.message  # полученное сообщение
            # peer_id = message['peer_id']  # ID пользователя куда отсылать ответ
            # from_id = message['from_id']  # ID пользователя который прислал сообщение
            text = message['text']  # Текст сообщения
            if len(text) > 0:
                # изучим текст сообщения
                message_tokens, token_length = parse_text(text, current_name)
                if (token_length != -1):
                    # Было обращение к боту
                    if (token_length > 0):  # ecть аргументы

                        if (message_tokens[0] == 'clusterize'):
                            if (token_length > 1):
                                clusterize(message, uploader, num_of_colors=int(message_tokens[1]))
                            else:
                                clusterize(message, uploader)
                        elif (message_tokens[0] == 'help'):
                            get_help(message)
                        else:
                            answer_to(message['peer_id'])
                    else:
                        ask_what(message)
                else:
                    answer_to(message['peer_id'])

if __name__ == '__main__':
    while True:
        try:  # Чтоб не падало
            print("(RE)START Bot-Server...")
            main()
        except Exception as err:
            full_stack_trace = traceback.format_exc()
            print("Error: {}".format(full_stack_trace))
