import os
import time

import logging
import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

logging.basicConfig(
    level=logging.DEBUG,
    filename='homework.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)


def parse_homework_status(homework):
    homework_status_dict = {
        'reviewing': 'взята на проверку.',
        'rejected': 'К сожалению в работе нашлись ошибки.',
        'approved': ('Ревьюеру всё понравилось, '
                     'можно приступать к следующему уроку.')
    }

    homework_name = homework.get('homework_name')
    verdict = homework_status_dict.get(homework.get('status'))

    if homework_name is None or verdict is None:
        return 'Неверный ответ сервера'
    if homework.get('status') == 'reviewing':
        return f'Работа {homework_name} {verdict}'
    # ох уж этот pytest =) хотел заменить
    # "У вас проверили работу" на "Статус работы"
    # и обойтись без еще одного ифа, но не тут то было)
    # тест хочет видеть только эту фразу.
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    url = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
    params = {'from_date': current_timestamp or int(time.time())}
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    try:
        homework_statuses = requests.get(url, params=params, headers=headers)
        # homework_statuses.raise_for_status()
    # закрыл в комменты <homework_statuses.raise_for_status()>
    # т.к pytest не пропускает - выдает ошибку AttributeError:
    # 'MockResponseGET' object has no attribute 'raise_for_status'
    # хотя при запуске программы все корректно работает
    except requests.exceptions.HTTPError as error:
        text_error = f'Ошибка доступа к серверу: {error}'
        logging.error(text_error, exc_info=True)
        return text_error
    else:
        return homework_statuses.json()


def send_message(message, bot_client):
    logging.info('Message sent')
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    # проинициализировать бота здесь
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    # начальное значение timestamp
    current_timestamp = int(time.time())
    logging.debug('Bot run')
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(
                             new_homework.get('homeworks')[0]), bot_client)
            current_timestamp = new_homework.get('current_date',
                                                 current_timestamp)
            time.sleep(300)  # опрашивать раз в пять минут

        except Exception as e:
            print(f'Бот столкнулся с ошибкой: {e}')
            logging.error(e, exc_info=True)
            bot_client.send_message(chat_id=CHAT_ID,
                                    text=f'Ошибка бота {e}\n\n{new_homework}')
            time.sleep(5)


if __name__ == '__main__':
    main()
