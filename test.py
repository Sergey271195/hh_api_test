import requests
import os
import re
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.abspath(''), '.env'))

BASE_URL = 'https://api.hh.ru/'
API_KEY = os.environ.get("API_KEY")
HEADERS = {'Authorization': f'Bearer {API_KEY}'} if API_KEY else None

class TestCase():

    test_counter = 0
    right_test_counter = 0
    wrong_test_counter = 0
    API_KEY = os.environ.get("API_KEY")
    BASE_URL = 'https://api.hh.ru/'
    HEADERS = {'Authorization': f'Bearer {API_KEY}'} if API_KEY else None
    tests_visual = []
    tests = []

    def __init__(self, path, wrong_test_message = None, right_test_message = None, description = None):
        self.path = path
        self.wrong_test_message = wrong_test_message
        self.right_test_message = right_test_message
        self.description = description
        TestCase.tests.append(self)

    @classmethod
    def prepare(cls):
        cls.tests_visual = ['.']*len(cls.tests)
        cls.test_counter = len(cls.tests)

    @classmethod
    def increase_wrong_counter(cls):
        cls.wrong_test_counter += 1
        return cls.wrong_test_counter

    @classmethod
    def increase_right_counter(cls):
        cls.right_test_counter += 1
        return cls.right_test_counter

    @classmethod
    def statistics(cls):
        print(f'\nПройдено тестов: {cls.right_test_counter} из {cls.test_counter}')
        print(f'Провалено тестов: {cls.wrong_test_counter} из {cls.test_counter}')
        print(' '.join([visual for visual in cls.tests_visual]))

    @classmethod
    def right_way(cls, instance, number):
        cls.increase_right_counter()
        cls.tests_visual[number] = '+'
        print("\nТест пройден".upper())
        print("Причина:", instance.right_test_message)
    
    @classmethod
    def wrong_way(cls, instance, number):
        cls.increase_wrong_counter()
        cls.tests_visual[number] = '-'
        print("Тест не пройден".upper())
        print("Причина:", instance.wrong_test_message)

    @classmethod
    def run_tests(cls):
        cls.prepare()
        for number, test in enumerate(cls.tests):
            print('\n', ' '.join([visual for visual in cls.tests_visual]))
            print(f"\nЗапсукаем тест {number + 1} из {cls.test_counter}")
            try:
                result = test.test()
                test.introduce()
                assert result
                cls.right_way(test, number)
            except AssertionError as a:
                cls.wrong_way(test, number)
        cls.statistics()

    
    def introduce(self):
        print('\nОписание'.upper())
        if self.description:
            print(self.description)

    def test(self):
        raise NotImplementedError()

    def make_request(self, params = None):
        if TestCase.HEADERS:
            request = requests.get(os.path.join(TestCase.BASE_URL, self.path), headers = TestCase.HEADERS, params = params)
        else:
            request = requests.get(os.path.join(TestCase.BASE_URL, self.path), params = params)
        try:
            json_response = request.json()
            return json_response
        except Exception as e:
            return None
    
    def make_request_all_pages(self, params = None, max_pages = None):
        unified_response = []
        page = 0
        if max_pages:
            print(f"Проверка первых {max_pages} страниц записей")
        while True:
            params['page'] = page
            if TestCase.HEADERS:
                request = requests.get(os.path.join(TestCase.BASE_URL, self.path), headers = TestCase.HEADERS, params = params)
            else:
                request = requests.get(os.path.join(TestCase.BASE_URL, self.path), params = params)
            try:
                json_response = request.json()
                unified_response.extend(json_response.get('items'))
                pages = int(json_response.get('pages'))
                page = int(json_response.get('page')) + 1
                if max_pages:
                    if page >= max_pages or page >= pages: break
                else:
                    if page >= pages: break
            except Exception as e:
                return None
        return unified_response

class TestCase_1(TestCase):

    def test(self):
        self.description = 'Базовые возможности:\nОжидаемое поведение: Запросы < java разработчик > и < разработчик java > возвращают одинаковое число записей'
        params_1 = {'text': 'java разработчик', 'search_field': 'name'}
        response_1 = self.make_request(params_1)
        params_2 = {'text': 'разработчик java', 'search_field': 'name'}
        response_2 = self.make_request(params_2)
        self.right_test_message = f'Запросы вернули одинаковое количество записей {response_1.get("found")} и {response_2.get("found")}'
        self.wrong_test_message = f'Запросы вернули различное количество записей {response_1.get("found")} и {response_2.get("found")}'
        return response_1.get('found') == response_2.get('found')

class TestCase_2(TestCase):

    def test(self):
        self.description = 'Поиск словосочетаний:\nОжидаемое поведение: Запросы < java разработчик > и < "java разработчик" > вернут различное число записей'
        params_1 = {'text': 'java разработчик', 'search_field': 'name'}
        response_1 = self.make_request(params_1)
        params_2 = {'text': '"java разработчик"', 'search_field': 'name'}
        response_2 = self.make_request(params_2)
        self.wrong_test_message = f'Запросы вернули одинаковое количество записей {response_1.get("found")} и {response_2.get("found")}'
        self.right_test_message = f'Запросы вернули различное количество записей {response_1.get("found")} и {response_2.get("found")}'
        return response_1.get('found') != response_2.get('found')

class TestCase_3(TestCase):

    def test(self):
        text_field = 'младший java разработчик'
        params = {'text': f'!"{text_field}"', 'search_field': 'name'}
        self.description = f'Учет словоформ:\nОжидаемое поведение: В каждой полученной по запросу < !"{text_field}" > вакансии содержится искомое словосочетание в искомой форме'
        json_response = self.make_request(params)
        answers = [text_field in response.get('name').lower() for response in json_response.get('items')]
        self.wrong_test_message = f'Не все записи содержат словосочетание < "{text_field}" > разработчик ({answers.count(True)} из {answers.count(False)}) '
        self.right_test_message = f'Все записи содержат словосочетание < "{text_field}" > разработчик ({len(answers)} из {len(answers)})'
        return all(answers)


class TestCase_4(TestCase):

    def test(self):
        text_field = 'гео'
        params = {'text': f'{text_field}*', 'search_field': 'name'}
        self.description = f'Поиск фрагмента слова:\nОжидаемое поведение: В каждой полученной по запросу < {text_field}* > вакансии содержатся слова, начинающиеся с < {text_field} >'
        json_response = self.make_request_all_pages(params, max_pages = 10)
        reg_exp = re.compile(r"гео\w+")
        words_set = set()
        for item in json_response:
            match_object = re.search(reg_exp, item.get('name').lower())
            if match_object:
                words_set.add(match_object.group(0))
        self.right_test_message = f"Во всех записях найдены слова, начинающиеся с < {text_field} >.\nСписок найденных слов:\n"
        self.right_test_message += '\n'.join([str(index) + '. ' + word for index, word in enumerate(words_set)])
        self.wrong_test_message = f"Не во всех записях найдены слова, гачинающиеся с < {text_field} >"
        return all([re.search(reg_exp, item.get('name').lower()) for item in json_response])


class TestCase_4(TestCase):

    def test(self):
        text_field = 'гео'
        params = {'text': f'{text_field}*', 'search_field': 'name'}
        self.description = f'Поиск фрагмента слова:\nОжидаемое поведение: В каждой полученной по запросу < {text_field}* > вакансии содержатся слова, начинающиеся с < {text_field} >'
        json_response = self.make_request_all_pages(params, max_pages = 10)
        reg_exp = re.compile(r"гео\w+")
        words_set = set()
        for item in json_response:
            match_object = re.search(reg_exp, item.get('name').lower())
            if match_object:
                words_set.add(match_object.group(0))
        self.right_test_message = f"Во всех записях найдены слова, начинающиеся с < {text_field} >.\nСписок найденных слов:\n"
        self.right_test_message += '\n'.join([str(index) + '. ' + word for index, word in enumerate(words_set)])
        self.wrong_test_message = f"Не во всех записях найдены слова, начинающиеся с <{text_field} >"
        return all([re.search(reg_exp, item.get('name').lower()) for item in json_response])


class TestCase_5(TestCase):

    def test(self):
        text_field = 'разработчик'
        synonym_field = 'developer'
        params = {'text': f'{text_field}', 'search_field': 'name'}
        self.description = f'Учет синонимов:\nОжидаемое поведение: В полученных по запросу < {text_field} > записях содержатся вакансии с < {synonym_field} >'
        json_response = self.make_request_all_pages(params, max_pages = 15)
        result = [synonym_field in item.get('name') for item in json_response]
        self.right_test_message = f"В {result.count(True)} из {len(result)} записей содержится синонимичное слово"
        self.wrong_test_message = f"Синонимичное слово не содержится ни в одной из вакансий"
        return any(result)

class TestCase_6(TestCase):

    def test(self):
        text_field = 'разработчик'
        synonym_field = 'developer'
        params = {'text': f'{text_field} not !{synonym_field}', 'search_field': 'name'}
        self.description = f'Исключение слова:\nОжидаемое поведение: В полученных по запросу < {text_field} not !{synonym_field} > записях не содержатся вакансии с < {synonym_field} >'
        json_response = self.make_request_all_pages(params, max_pages = 15)
        result = [synonym_field in item.get('name') for item in json_response]
        self.wrong_test_message = f"В {result.count(True)} из {len(result)} записей содержится синонимичное слово"
        self.right_test_message = f"Синонимичное слово не содержится ни в одной из вакансий"
        return not any(result)


class TestCase_7(TestCase):

    def test(self):
        first_field = 'c++'
        second_field = 'c#'
        params = {'text': f'!{first_field} or !{second_field}', 'search_field': 'name'}
        self.description = f'Исключение слова:\nОжидаемое поведение: В полученных по запросу < {first_field} or {second_field} > записях содержатся вакансии с < {first_field} > либо < {second_field} >'
        json_response = self.make_request_all_pages(params, max_pages = 15)
        result = [(first_field in item.get('name') or second_field in item.get('name')) for item in json_response]
        self.right_test_message = f"Во всех записях содержится хотя бы одно из искомых слов"
        self.wrong_test_message = f"Не во всех вакансиях содержится хотя бы одно из искомых слов"
        return not any(result)

class TestCase_8(TestCase):

    def test(self):
        random_param = 'антенны'
        params = {'text': f'{random_param}', 'search_field': 'name'}
        random_response = self.make_request(params)
        first_entry = random_response.get('items')[0]
        print(f"Получаем первую вакансию по запросу < {random_param} >")
        _id = first_entry.get('id')
        name = first_entry.get('name')
        company_id = first_entry.get('employer').get('id')
        company_name = first_entry.get('employer').get('name')
        print(f"Параметры полученной вакансии:\n\n id: {_id}\n name: {name}\n company_id: {company_id}\n company_name: {company_name}\n")
        params = {'text': f'!ID:{_id} AND COMPANY_NAME:({company_name}) AND !COMPANY_ID:{company_id} AND NAME:({name})'}
        random_response = self.make_request(params)
        self.description = f'Поиск по полям:\nОжидаемое поведение: В полученной по запросу < !ID:{_id} AND COMPANY_NAME:({company_name}) AND !COMPANY_ID:{company_id} AND NAME:({name}) > записи мы получем первоначальную вакансию'
        self.right_test_message = f"В ответе на запрос вернулась первоначальная вакансия"
        self.wrong_test_message = f"В ответе на запрос вернулась иная вакансия либо вакансия не была найдена"
        if len(random_response.get('items')) >= 1:
            return _id == random_response.get('items')[0].get('id')

class TestCase_9(TestCase):

    def test(self):
        random_param = 'гора'
        params = {'text': f'{random_param}', 'search_field': 'name'}
        random_response = self.make_request(params)
        first_entry = random_response.get('items')[0]
        print(f"Получаем первую вакансию по запросу < {random_param} >")
        _id = first_entry.get('id')
        name = first_entry.get('name')
        company_id = first_entry.get('employer').get('id')
        company_name = first_entry.get('employer').get('name')
        print(f"Параметры полученной вакансии:\n\n id: {_id}\n name: {name}\n company_id: {company_id}\n company_name: {company_name}\n")
        params = {'text': f'!ID:{_id} AND COMPANY_NAME:({company_name}) AND !COMPANY_ID:{int(company_id)+1} AND NAME:({name})'}
        random_response = self.make_request(params)
        self.description = f'Поиск по полям:\nОжидаемое поведение: В полученной по запросу < !ID:{_id} AND COMPANY_NAME:({company_name}) AND !COMPANY_ID:({company_id}+1) AND NAME:({name}) > записи мы НЕ получем первоначальную вакансию'
        self.right_test_message = f"В ответе на запрос не вернулось ни одной вакансии"
        self.wrong_test_message = f"В ответе на запрос вернулась первоначальная вакансия"
        if len(random_response.get('items')) >= 1:
            print(random_response.get('items')[0].get('id'))
            return _id != random_response.get('items')[0].get('id')
        return True


class TestCase_10(TestCase):

    def test(self):
        params = {'text': '', 'search_field': 'name'}
        json_response = self.make_request(params)
        self.description = f'Передача пустового текстового поля:\nОжидаемое поведение: Пустой запрос вернет все опубликованные вакансии' 
        self.right_test_message = f"В ответе на запрос вернулось более 500_000 вакансий"
        self.wrong_test_message = f"В запросе было проигнорировано текстовое поле"
        return json_response.get('found') > 500_000

class TestCase_11(TestCase):

    def test(self):
        number = 4097
        params = {'text': '1'*number}
        json_response = self.make_request(params)
        self.description = f'Проверка поля на большое количество символов:\nОжидаемое поведение: В ответе на запрос длиной {number} и более символов вернется ошибка'
        self.right_test_message = f"В ответе на запрос не вернулась ошибка. Error: {json_response.get('errors')}"
        self.wrong_test_message = f"В запросе было проигнорировано текстовое поле"
        return json_response.get('errors')
        

class TestCase_12(TestCase):

    def test(self):
        number = 4096
        params = {'text': '1'*number}
        empty_params = {'text': ''}
        json_response_1 = self.make_request(params)
        json_response_2 = self.make_request(empty_params)
        self.description = f'Проверка поля на большое количество символов:\nОжидаемое поведение: В ответе на запрос длиной {number} текстовое поле будет проигнорировано, запрос вернет все опубликованные вакансии'
        self.right_test_message = f"В ответе на запрос вернулось такое же количество вакансий, как и на запрос с пустым текстовым полем"
        self.wrong_test_message = f"В ответе на данный запрос и на запрос с пустым текстовым полем вернулось различное число вакансий ( {json_response_1.get('found')} и {json_response_2.get('found')} )"
        return json_response_1.get('found') == json_response_2.get('found')

class TestCase_13(TestCase):

    def test(self):
        text_field = "/../,/.,/.m,m,.,;;.;.;.l-0909-0998890[;];'/./.;..;.;;.,ml,lp."
        print(f'Случайный набор символов: {text_field}')
        params = {'text': text_field}
        json_response = self.make_request(params)
        self.description = f'Проверка поля на случайный набор символов:\nОжидаемое поведение: В ответе на запрос, содержащий случайный набор символов, текстовое поле будет проигнорировано, запрос вернет все опубликованные вакансии'
        self.right_test_message = f"В ответе на запрос вернулось такое же количество вакансий, как и на запрос с пустым текстовым полем"
        self.wrong_test_message = f"В ответе на данный запрос не вернулось ни одной вакансии"
        return len(json_response.get('items')) > 0


class TestCase_14(TestCase):

    def test(self):
        text_field = "Жұмыс"
        params = {'text': text_field, }
        json_response = self.make_request(params)
        self.description = f'Проверка поля на казахский язык:\nОжидаемое поведение: В ответе на запрос, содержащий слово на казахском языке {text_field}, вернется более 1 вакансии'
        self.right_test_message = f"В ответе на запрос вернулось более 1 вакансии ( {json_response.get('found')} )"
        self.wrong_test_message = f"В ответе на данный запрос не вернулось ни одной вакансии"
        return json_response.get('found') > 0


class TestCase_15(TestCase):

    def test(self):
        text_field = "лікар"
        params = {'text': text_field, }
        json_response = self.make_request(params)
        self.description = f'Проверка поля на украинский язык:\nОжидаемое поведение: В ответе на запрос, содержащий слово на украинском языке {text_field}, вернется более 1 вакансии'
        self.right_test_message = f"В ответе на запрос вернулось более 1 вакансии ( {json_response.get('found')} )"
        self.wrong_test_message = f"В ответе на данный запрос не вернулось ни одной вакансии"
        return json_response.get('found') > 0


class TestCase_16(TestCase):

    def test(self):
        text_field = "開發商"
        params = {'text': text_field,}
        json_response = self.make_request(params)
        self.description = f'Проверка поля на китайский язык:\nОжидаемое поведение: В ответе на запрос, содержащий слово на китайском языке {text_field}, текстовое поле будет проигнорировано, вернется список всех опубликованных вакансий'
        self.right_test_message = f"Текстовое поле было проигнорировано. В ответе на запрос вернулось более 1 вакансии ( {json_response.get('found')} )"
        self.wrong_test_message = f"В ответе на данный запрос не вернулось ни одной вакансии"
        return json_response.get('found') > 0


class TestCase_17(TestCase):

    def test(self):
        text_field = "java"
        params = {'text': text_field,}
        json_response = requests.post(os.path.join(self.BASE_URL, self.path), params = params)
        self.description = f'Проверка поля на POST метод:\nОжидаемое поведение: В ответе на POST запрос должна вернуться ошибка со статусом 403'
        self.right_test_message = f"Запрос вернул ошибку 403 Forbidden"
        self.wrong_test_message = f"Запрос прошел без ошибки"
        return json_response.status_code == 403

class TestCase_18(TestCase):

    def test(self):
        text_field = "java"
        params = {'test': text_field,}
        json_response = self.make_request(params)
        self.description = f'Опечатка при указании названия поля (test вместо text):\nОжидаемое поведение: Текстовое поле будет проигнорировано, вернется список всех опубликованных вакансий'
        self.right_test_message = f"В запросе было проигнорировано текстовое поле. Запрос вернул все опубликованные вакансии."
        self.wrong_test_message = f"Текстовое поле не было проигнорировано. Запрос вернул только искомые вакансии"
        return json_response.get('found') > 500_000

class TestCase_19(TestCase):

    def test(self):
        text_field_1 = "ёлка"
        text_field_2 = "елка"
        params_1 = {'text': f"!{text_field_1}", 'search_field': 'company_name'}
        params_2 = {'text': f"!{text_field_2}", 'search_field': 'company_name'}
        json_response_1 = self.make_request(params_1)
        json_response_2 = self.make_request(params_2)
        self.description = f'Буква ё в запросе:\nОжидаемое поведение: Запрос вернет результаты, содержащие буквы е и ё'
        self.right_test_message = f"Запрос < {text_field_1} > вернул такое же число записей как и < {text_field_2} >"
        self.wrong_test_message = f"Запрос < {text_field_1} > вернул иное число записей по сравнению с запросом < {text_field_2} > ({json_response_1.get('found')} и {json_response_2.get('found')})"
        return json_response_1.get('found') == json_response_2.get('found')


class TestCase_20(TestCase):

    def test(self):
        text_field_1 = "Яндекс"
        text_field_2 = "Янтекс"
        params_1 = {'text': f"{text_field_1}", 'search_field': 'company_name'}
        params_2 = {'text': f"{text_field_2}", 'search_field': 'company_name'}
        json_response_1 = self.make_request(params_1)
        json_response_2 = self.make_request(params_2)
        self.description = f'Опечатка в запросе:\nОжидаемое поведение: Опечатка будет определена. Запрос вернет результаты такое же число записей, как и запрос без опечатки'
        self.right_test_message = f"Запрос < {text_field_1} > вернул такое же число записей как и < {text_field_2} >"
        self.wrong_test_message = f"Запрос < {text_field_1} > вернул иное число записей по сравнению с запросом < {text_field_2} > ({json_response_1.get('found')} и {json_response_2.get('found')})"
        return json_response_1.get('found') == json_response_2.get('found')

class TestCase_21(TestCase):

    def test(self):
        text_field_1 = "ЯНДЕКС"
        text_field_2 = "яндекс"
        params_1 = {'text': f"{text_field_1}", 'search_field': 'company_name'}
        params_2 = {'text': f"{text_field_2}", 'search_field': 'company_name'}
        json_response_1 = self.make_request(params_1)
        json_response_2 = self.make_request(params_2)
        self.description = f'Проверка поля на регистр:\nОжидаемое поведение: Запрос вернет одинаковое число записей независимо от регистра'
        self.right_test_message = f"Запрос < {text_field_1} > вернул такое же число записей как и < {text_field_2} >"
        self.wrong_test_message = f"Запрос < {text_field_1} > вернул иное число записей по сравнению с запросом < {text_field_2} > ({json_response_1.get('found')} и {json_response_2.get('found')})"
        return json_response_1.get('found') == json_response_2.get('found')

if __name__ == '__main__':
    tc1 = TestCase_1(
        path = 'vacancies',
    )
    tc2 = TestCase_2(
        path = 'vacancies',
    )
    tc3 = TestCase_3(
        path = 'vacancies',
    )
    tc4 = TestCase_4(
        path = 'vacancies',
    )
    tc5 = TestCase_5(
        path = 'vacancies',
    )
    tc6 = TestCase_6(
        path = 'vacancies',
    )
    tc7 = TestCase_7(
        path = 'vacancies',
    )
    tc8 = TestCase_8(
        path = 'vacancies',
    )
    tc9 = TestCase_9(
        path = 'vacancies',
    )
    tc10 = TestCase_10(
        path = 'vacancies',
    )
    tc11 = TestCase_11(
        path = 'vacancies',
    )
    tc12 = TestCase_12(
        path = 'vacancies',
    )
    tc13 = TestCase_13(
        path = 'vacancies',
    )
    tc14 = TestCase_14(
        path = 'vacancies',
    )
    tc15 = TestCase_15(
        path = 'vacancies',
    )
    tc16 = TestCase_16(
        path = 'vacancies',
    ) 
    tc17 = TestCase_17(
        path = 'vacancies',
    )
    tc18 = TestCase_18(
        path = 'vacancies',
    )
    tc19 = TestCase_19(
        path = 'vacancies',
    )
    tc20 = TestCase_20(
        path = 'vacancies',
    )
    tc21 = TestCase_21(
        path = 'vacancies',
    )
    TestCase.run_tests()