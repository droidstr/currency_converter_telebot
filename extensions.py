import requests
import datetime
import lxml.html
import json
from config import CURRATE_TOKEN


class APIException(Exception):
    pass


class WrongCommandException(APIException):
    pass


class UnavailableCurrencyException(APIException):
    pass


class ServerResponseException(APIException):
    pass


class Converter:
    def __init__(self):
        self.currencies_dict = API.get_currencies_dict()
        self.available_currencies_list = API.get_available_currencies_list()
        self.last_update_time = datetime.datetime.now()
        self.pairs_cache = dict()
        self.currencies = self.make_currencies_dict()

    def __str__(self):
        return '\n'.join(self.currencies)

    def make_currencies_dict(self):
        result = dict()
        for literal in self.available_currencies_list:
            if literal in self.currencies_dict:
                result.update({self.currencies_dict[literal]: literal})
        return result

    def get_price(self, command):
        try:
            commands = command.split()
            if len(commands) < 3:
                raise WrongCommandException(
                    'Введено недостаточно данных. Введиете команду в формате <имя валюты, '
                    'цену которой вы хотите узнать> <имя валюты, в которой нужно узнать цену '
                    'первой валюты> <количество первой валюты>.')
            elif len(commands) > 3:
                raise WrongCommandException(
                    'Введено слишком много данных. Введиете команду в формате <имя валюты, '
                    'цену которой вы хотите узнать> <имя валюты, в которой нужно узнать цену '
                    'первой валюты> <количество первой валюты>.')
            else:
                try:
                    base, quote = self.currencies[commands[0]], self.currencies[commands[1]]
                    amount = float(commands[2])
                except ValueError:
                    raise WrongCommandException('Количество переводимой валюты должно быть числом')
                except KeyError:
                    raise WrongCommandException(
                        'Указана неподдерживаемая валюта. Чтобы узнать список поддерживаемых валют, используйте команду /values')
            if (datetime.datetime.now() - self.last_update_time) > datetime.timedelta(hours=1):
                self.pairs_cache = dict()
                self.last_update_time = datetime.datetime.now()
            if not (base + quote in self.pairs_cache):
                self.pairs_cache[base + quote] = API.get_price(base, quote)
            result = self.pairs_cache[base + quote] * amount
            reply = f'Цена {commands[2]} {commands[0]} в {commands[1]} - {result}'
        except APIException as error_text:
            reply = error_text
        finally:
            return reply




class API:
    @staticmethod
    def get_currencies_dict():  # получаем с википедии перечень валют и тикеров
        page = requests.get(
            'https://ru.wikipedia.org/wiki/%D0%A1%D0%BF%D0%B8%D1%81%D0%BE%D0%BA_%D0%B7%D0%BD%D0%B0%D0%BA%D0%BE%D0%B2_%D0%B2%D0%B0%D0%BB%D1%8E%D1%82')
        tree = lxml.html.document_fromstring(page.text)
        names = list(a.text for a in tree.findall('.//*[@id="mw-content-text"]/div[1]/table[2]/tbody/tr/td[1]/a'))
        countries = list(''.join(list(
            b.text for b in a.findall('.//a') if b.text
        )) for a in tree.findall(
            './/*[@id="mw-content-text"]/div[1]/table[2]/tbody/tr/td[2]'
        ))
        literals = list(a.text.strip() for a in tree.findall(
            './/*[@id="mw-content-text"]/div[1]/table[2]/tbody/tr/td[3]'
        ))
        result = dict()
        for i in range(len(countries)):
            name = '_'.join(names[i].split())
            if names.count(names[i]) > 1 and countries[i] not in ['Россия', 'США']:
                name += f"({'_'.join(countries[i].split())})"
            for literal in literals[i].split(','):
                result.update({literal: name})
        return result

    @staticmethod
    def get_available_currencies_list():
        response = requests.get(f'https://currate.ru/api/?get=currency_list&key={CURRATE_TOKEN}')
        status = json.loads(response.content)['status']
        if int(status) != 200:
            raise ServerResponseException('Something went wrong')
        text = json.loads(response.content)['data']
        literals = set()
        for pair in text:
            literals.add(pair[:3])
            literals.add(pair[3:])
        return list(literals)

    @staticmethod
    def get_price(base, quote):
        response = requests.get(f'https://currate.ru/api/?get=rates&pairs={base+quote}&key={CURRATE_TOKEN}')
        status = json.loads(response.content)['status']
        if int(status) != 200:
            if int(status) == 500:
                raise ServerResponseException('Попробуйте другую пару')
            else:
                raise ServerResponseException('Что-то пошло не так при попытке связаться'
                                              'с сервером. Пожалуйста, попробуйте позже.')
        return float(json.loads(response.content)['data'][base+quote])


