import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import bot_token, chat_id
bot = Bot(bot_token)

class Form(StatesGroup):
    url = State()
    delete = State()


dp = Dispatcher(bot, storage=MemoryStorage())

kb = ReplyKeyboardMarkup(resize_keyboard=True)
kb.add(KeyboardButton("\U0001F514  Добавить профиль")).insert(KeyboardButton("\u274C  Удалить профиль"))
kb.add(KeyboardButton("\U0001F4D6  Посмотреть все профили"))


last_tweets = {}
options = webdriver.ChromeOptions()
service = Service(executable_path="chromedriver/chromedriver.exe")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--headless")
driver = webdriver.Chrome(service=service, options=options)

first_tweet = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div/div/div[3]/div/div/section/div/div/div[1]/div/div/div/article/div/div/div/div[2]/div[2]"
pinned_message = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div/div/div[3]/div/div/section/div/div/div[1]/div/div/div/article/div/div/div/div[1]/div/div/div/div/div[2]/div/div/div/span"
last_tweet_with_pinned_message = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div/div/div[3]/div/div/section/div/div/div[2]/div/div/div/article/div/div/div/div[2]/div[2]/div[2]/div[1]/div"
last_tweet_without_pinned_message = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div/div/div[3]/div/div/section/div/div/div[1]/div/div/div/article/div/div/div/div[2]/div[2]/div[2]/div[1]"
xpath_for_click_without_pinned_message = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div/div/div[3]/div/div/section/div/div/div[1]/div/div/div/article/div"
xpath_for_click_with_pinned_message = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div/div/div[3]/div/div/section/div/div/div[2]/div/div/div/article/div/div/div/div[2]/div[2]"

def element_exist(element):
    try:
        driver.find_element(By.XPATH, element)
        return True
    except:
        return False

async def delete_prof(url):
    if url in last_tweets.keys():
        last_tweets.pop(url)
        await bot.send_message(chat_id=chat_id, text=f"Профиль {url} был успешно удален!")
    else:
        await bot.send_message(chat_id=chat_id, text="Такого профиля нет в списке!")

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.answer("Введите ссылку на профиль для добавления!", reply_markup=kb)

@dp.message_handler(commands=['add'])
async def add_profile(message: types.Message):
    await Form.url.set()
    await message.answer("Введите ник профиля ( для отмены нажмите --> /cancel )")

@dp.message_handler(commands=['delete'])
async def delete(message: types.Message):
    await Form.delete.set()
    await message.answer("Введите ник профиля ( для отмены нажмите --> /cancel )")


@dp.message_handler(state='*', commands=['cancel'])
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.finish()
    await message.reply('Отменено')

@dp.message_handler(state=Form.url)
async def process_name(message: types.Message, state: FSMContext):
    await state.finish()
    url = f"https://twitter.com/{message.text}"
    await profile_adding(url)

@dp.message_handler(state=Form.delete)
async def delete_profile(message: types.Message, state: FSMContext):
    await state.finish()
    url = f"https://twitter.com/{message.text}"
    await delete_prof(url)



@dp.message_handler(commands=['profiles'])
async def profiles_command(message: types.Message):
    if len(last_tweets) < 1:
        await message.answer("У вас нет добавленных профилей!")
    else:
        i = 1
        profiles_answer = ""
        for profile in last_tweets.keys():
            profiles_answer = profiles_answer + f"{i}. {profile}\n"
            i += 1
        await message.answer(profiles_answer)


@dp.message_handler()
async def wait_for_buttons(message: types.Message):
    if message.text == "Посмотреть все профили":
        if len(last_tweets) < 1:
            await message.answer("У вас нет добавленных профилей!")
        else:
            i = 1
            profiles_answer = ""
            for profile in last_tweets.keys():
                profiles_answer = profiles_answer + f"{i}. {profile}\n"
                i += 1
            await message.answer(profiles_answer)

    elif message.text == "Добавить профиль":
        await Form.url.set()
        await message.answer("Введите ник профиля ( для отмены нажмите --> /cancel )")

    elif message.text == "Удалить профиль":
        await Form.delete.set()
        await message.answer("Введите ник профиля, который хотите удалить!")

    else:
        await message.answer("Я вас не понял, воспользуйтесь кнопками!")


async def profile_adding(url):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, first_tweet)))
        if element_exist(pinned_message):
            div_text = driver.find_element(By.XPATH, last_tweet_with_pinned_message)
        else:
            div_text = driver.find_element(By.XPATH, last_tweet_without_pinned_message)
        last_tweets[url] = div_text.text
        await bot.send_message(chat_id=chat_id, text="Профиль успешно добавлен!")
    except Exception as exp:
        await bot.send_message(chat_id=chat_id, text="Произошла ошибка при добавлении, проверьте ссылку на профиль!")
        print(exp)


async def parser():
    while True:
        if len(last_tweets) < 1:
            await asyncio.sleep(10)
        else:
            try:
                for profile in last_tweets.copy():
                    driver.get(url=profile)
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, first_tweet)))
                    if element_exist(pinned_message):
                        div_text = driver.find_element(By.XPATH, last_tweet_with_pinned_message)
                    else:
                        div_text = driver.find_element(By.XPATH, last_tweet_without_pinned_message)

                    if div_text.text != last_tweets[profile]:
                        tweet_text = div_text.text
                        if element_exist(pinned_message):
                            test_element = driver.find_element(By.XPATH, xpath_for_click_with_pinned_message)
                        else:
                            test_element = driver.find_element(By.XPATH, xpath_for_click_without_pinned_message)
                        driver.execute_script("arguments[0].scrollIntoView();", test_element)
                        test_element.click()
                        tweet_url = driver.current_url
                        await bot.send_message(chat_id=chat_id, text=f"Новое сообщение от {'@' + profile[20:]}:\n{tweet_text}\n\nСсылка на твитт: {tweet_url}")
                        last_tweets[profile] = tweet_text
                    await asyncio.sleep(10)
            except Exception as ex:
                print(ex)
                await bot.send_message(chat_id=chat_id, text="Произошла ошибка при парсе!")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(parser())
    executor.start_polling(dp, skip_updates=True)