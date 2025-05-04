#Импорт необходимых модулей
import asyncio
import os
import csv
import json
import pandas as pd
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.filters import Command

#Глобальные переменные
sentences = [] #предложения из исходных .xlsx-файлов
viewed_sentences = {} #обработанные предложения; загружаются в .json-файл и далее не выдаются другим разметчикам
current_index = {} #Индекс преддожения для разметчика
user_words = {} #Перед выбором Да/Нет?не знаю предложения сохраняются
CORPUS = "" #итоговые размеченные данные
VIEWED_JSON = "" #тут сохраняются просмотренные хотя бы одним разметчиком предложения
THE_ID = 0 #телеграмм-id, куда отправляются сохраненные пользователями результаты

#Здесь будут регистрироваться обработчики команд (=хендлеры)
router = Router()

#Клавиатуры
#Кнопка, выгружающая первое предложение
start_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Продолжить")]],
    resize_keyboard=True
)
#Кнопки, которые либо выводят следующий глагол, либо дают разметчику обработать еще одно слово
word_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Ввести еще глагол")], [KeyboardButton(text="Следующее предложение")]],
    resize_keyboard=True
)
#Выбор, употреблен глагол метафорично или нет
choice_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Нет"), KeyboardButton(text="Да"), KeyboardButton(text="Не знаю")]],
    resize_keyboard=True
)

#Обработчик команды /helps - справка по работе с ботом и по разметке
@router.message(Command("helps"))
async def help_command(message: Message):
    help_text = (
        "Этот бот помогает размечать глаголы\n\n"
        "Команды:\n"
        "/start — начать работу\n"
        "/helps — показать это сообщение\n"
        "/export - сохранить все предложения, что вы разметили\n\n"
        "Что ищем:\n"
        "-глаголы, в том числе инфинитивы (то есть форма глагола, отвечающая на вопрос что делать? - убивать)\n"
        "-деепричастия (то есть слова, отвечающие на вопросы что сделав? - убрав, что делая? - убирая)\n"
        "-причастия (то есть слова, отвечающие на вопросы что делающий? - покупающий, что сделавший? - купивший)\n\n"
        "Как пользоваться ботом:\n"
        "1. Нажмите 'Продолжить', чтобы получить предложение.\n"
        "2. Вам будет дано предложение, а после тире, глаголы, которые необходимо разметить. Вбейте первый глагол, который вам попался, с маленькой буквы в инфинитиве (форма, отвечающая на вопрос что делать?).\n\n"
        "Если сомневаетесь, какой у глагола инфинитив, копируете глагол, идете по этой ссылке https://ruscorpora.ru/ и вставляете глагол в строку поиска. Вам выдается информация о глаголе, и в пункте 'Лемма' будет показан инфинитив\n\n"
        "3. Далее вам нужно будет ввести номер этого слова в предложении. То есть, вы считаете слова в предложении, начиная с самого первого, и указываете, какое ваше слово по счету. Запятые, кавчки, тире и т.п. считаются как отдельные слова.\n\n"
        "4. Дальше бот задаст вопрос, употреблен ли глагол метафорично. Выберите 'Да', если глагол употреблен метафорично или 'Нет', если не метафорично или буквально, 'Не знаю', если сомневаетесь.\n\n"
        "Не уверены, как употреблен глагол - ознакомьтесь, пожалуйста, еще раз с инструкцией (есть в описании бота и по ссылке - https://docs.google.com/document/d/1AUfTp2h8kG3sgZsHnrfNyPGP4dMPXd75z5Nhilu2r2Q/edit?tab=t.0), а также посмотрите вот по этим двум ссылочкам, какое у глагола буквальное значение - https://feb-web.ru/feb/mas/mas-abc/default.asp (Словарь русского языка (СРЯ)), https://ozhegov.info/slovar/ (Словарь Ожегова (ТСРЯ))\n\n"
        "5. Если есть еще глагол, тыкните на 'Ввести еще глагол' и повторите процедурку. В противном случае перейдите к следующему предложению ('Следующее предложение').\n"
        "6. Когда вы захотели завершить работу с ботом (например, вы разметили нужное количество предложений или продолжите на следующий день) - выберите слева в меню команду 'сохранить', и бот сохранит все, что вы разметили.\n"
    )
    await message.answer(help_text)

#Обработчик команды /start - начало работы с ботом
@router.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Нажмите 'Продолжить', чтобы начать.", reply_markup=start_keyboard)

#Обработчик команды /export - сохраняет размеченные аннотатором предложения и отправляет мне в телеграмм
@router.message(Command("export"))
async def export_handler(message: Message, bot: Bot):
    user_id = message.from_user.id
    #Если строчка с глаголом Х еще не до конца обработана, не дает сохранить результат
    if user_id in user_words and "numbertoken" not in user_words[user_id]:
        await message.answer("Закончите работу с текущим предложением, а затем сохраните ваш результат.")
        return

    if os.path.exists(CORPUS):
        await bot.send_document(chat_id=THE_ID, document=FSInputFile(CORPUS))
    if os.path.exists(VIEWED_JSON):
        await bot.send_document(chat_id=THE_ID, document=FSInputFile(VIEWED_JSON))

    await message.answer("Ваши предложения были успешно сохранены. Спасибо за участие!")

#Обработчик команды статистики /statistics - указывает разметчику, сколько предложений он обработал
@router.message(Command("statistics"))
async def stats_handler(message: Message):
    user_id = str(message.from_user.id)

    #Проверка, есть ли файл с корпусом
    if not os.path.exists(CORPUS):
        await message.answer("Файл с разметкой пока не создан.")
        return

    #Считаем уникальные предложения пользователя в конечном .csv-файле
    sentences_seen = set()
    with open(CORPUS, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if row and row[0] == user_id:
                sentence = row[1]
                sentences_seen.add(sentence)

    count = len(sentences_seen)
    await message.answer(f"Вы уже разметили {count} предложений.")

#Обработчик кнопки "Продолжить"
@router.message(F.text == "Продолжить")
async def continue_handler(message: Message):
    user_id = message.from_user.id
    #Ищет предложение, которое еще не было никем размечено, выдает пользователю
    for SENTENCE, SPHERE, VERBS in sentences:
        if SENTENCE not in viewed_sentences:
            viewed_sentences.setdefault(SENTENCE, []).append(user_id)
            with open(VIEWED_JSON, "w", encoding="utf-8") as f:
                json.dump(viewed_sentences, f, ensure_ascii=False, indent=4)

            current_index[user_id] = (SENTENCE, SPHERE, VERBS)
            await message.answer(f"{SENTENCE} - {VERBS}")
            await message.answer("Введите инфинитив глагола:")
            return

    await message.answer("Все предложения закончились!", reply_markup=start_keyboard)

#Если пользователь хочет обработать еще один глагол
@router.message(F.text == "Ввести еще глагол")
async def more_verbs(message: Message):
    await message.answer("Введите инфинитив глагола:")

#Если пользователь хочет перейти к следующему предложению
@router.message(F.text == "Следующее предложение")
async def next_sentence(message: Message):
    await continue_handler(message)

#Разметчик делает выбор, употреблен ли глагол метафорично, итоговая строчка записывается в .csv-файл
@router.message(F.text.in_(["Нет", "Да", "Не знаю"]))
async def handle_choice(message: Message):
    user_id = message.from_user.id

    METAPHORIC = {"Нет": "0", "Да": "1", "Не знаю": "2"}[message.text]

    if user_id in user_words:
        data = user_words[user_id]
        with open(CORPUS, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([user_id, data["sentence"], data["sphere"], data["verb"], data["numbertoken"], METAPHORIC])

    await message.answer("Хотите ввести еще глагол или перейти дальше?", reply_markup=word_keyboard)

#
@router.message()
async def handle_input(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()

    if user_id in user_words and "numbertoken" not in user_words[user_id]:
        if text.isdigit():
            user_words[user_id]["numbertoken"] = int(text)
            await message.answer("Глагол употреблен метафорично?", reply_markup=choice_keyboard)
        else:
            await message.answer("Пожалуйста, введите номер глагола (число):")
        return

    if user_id in current_index:
        VERB = text
        SENTENCE, SPHERE, _ = current_index[user_id]
        user_words[user_id] = {"sentence": SENTENCE, "sphere": SPHERE, "verb": VERB}
        await message.answer("Введите номер глагола в предложении:")


#Основная функция
async def main():
    global sentences, viewed_sentences, current_index, user_words, CORPUS, VIEWED_JSON, THE_ID
    #Загружаем переменные окружения
    API_TOKEN = os.getenv("API_TOKEN")
    EXCEL_FOLDER = os.getenv("EXCEL_FOLDER")
    VIEWED_JSON = os.getenv("VIEWED_JSON")
    CORPUS = os.getenv("CORPUS")
    THE_ID = int(os.getenv("THE_ID"))

    #Проверяем наличие всех переменных
    if not all([API_TOKEN, EXCEL_FOLDER, VIEWED_JSON, CORPUS, THE_ID]):
        raise RuntimeError("Не все переменные окружения заданы!")

    #Загрузка данных из .xlsx-файлов
    def load_sentences():
        result = {}
        for file in os.listdir(EXCEL_FOLDER):
            if file.endswith(".xlsx"):
                try:
                    df = pd.read_excel(os.path.join(EXCEL_FOLDER, file), engine="openpyxl")
                    if {"Full context", "Sphere", "Center"}.issubset(df.columns):
                        for _, row in df.iterrows():
                            SENTENCE = row["Full context"]
                            SPHERE = row["Sphere"]
                            VERBTOKEN = row["Center"]
                    
                            #Если предложение уже есть, добавляем слово к существующим
                            if SENTENCE in result:
                                result[SENTENCE][0].add(VERBTOKEN)
                            else:
                                result[SENTENCE] = (set([VERBTOKEN]), SPHERE)
                    else:
                        raise KeyError("Файл Excel должен содержать колонки 'SENTENCE', 'SPHERE' и 'VERBTOKEN'")
                except Exception as e:
                    print(f"Ошибка при чтении файла {file}: {e}")

        #Преобразуем в формат списка кортежей
        return [(s, sp, ", ".join(v)) for s, (v, sp) in result.items()]

    #Загружаем просмотренных предложений
    def load_viewed():
        if os.path.exists(VIEWED_JSON):
            with open(VIEWED_JSON, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except:
                    return {}
        return {}
    sentences = load_sentences()
    viewed_sentences = load_viewed()
    current_index = {}
    user_words = {}
    #Инициализация бота
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    #Запуск
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())