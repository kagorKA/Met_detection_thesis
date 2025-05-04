from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from time import sleep

driver_path = "/usr/local/bin/chromedriver"
#Путь к драйверу браузера
servis = Service(driver_path)

driver = webdriver.Chrome(service=servis)


#Открываем страницу

driver.get('URL')
sleep(20)

pages = driver.find_element(By.XPATH, '//a[text()="X"]') #X - следующая по счету страница

for i in range(10):

#Получаем все ссылки на странице
    buttons = driver.find_elements(By.XPATH, "//a[contains(text(), 'Все примеры')]")

#Перебираем все ссылки
    for exemp_button in buttons:
        try:
        #Открываем ссылку в новой вкладке
            exemp_button.send_keys(Keys.COMMAND + Keys.RETURN) 
        
        #Переключаемся на последнюю вкладку
            WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(len(driver.window_handles)))  #Ждем, пока откроется новая вкладка
            driver.switch_to.window(driver.window_handles[-1])  #Переходим на новую вкладку
            sleep(8)

            driver.find_element(By.XPATH, '//button[text()="Скачать "]').click()
            sleep(10)

            try:
                driver.find_element(By.XPATH, '//button[text()="Продолжить"]').click()
                sleep(5)
            except NoSuchElementException:
                print('No need to continue')
#Сначала пропускаем авторизацию, затем качаем тексты
    
            excel_button = driver.find_element(By.XPATH, '//button[text()="Excel"]')
            excel_button.click()
            sleep(30)

        #Закрываем текущую вкладку
            driver.close()
        
        #Переключаемся обратно на основную страницу
            driver.switch_to.window(driver.window_handles[0])
    
        except Exception as e:
            print(f"Ошибка при обработке ссылки: {e}")


    pages.click()
    pages = driver.find_element(By.XPATH, f'//a[text()="{i + X+1}"]')
    sleep(30)

#Закрываем браузер
driver.quit()

print (f'файл скачан')
