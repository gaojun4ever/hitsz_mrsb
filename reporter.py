"""
HITSZ 每日上报
"""
import json
import logging
from configparser import ConfigParser
from urllib.parse import quote

import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [ %(levelname)s ] %(message)s')


class Reporter(object):
    def __init__(self):
        self.headers = {
            'Host': 'student.hitsz.edu.cn',
            # 'Cookie': 'JSESSIONID=A23D1CDA37AA6A8FCCA233C60DF78AB5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.83 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'X-Requested-With': 'XMLHttpRequest'
        }

    @staticmethod
    def get_user_list():
        config = ConfigParser()
        config.read('users.ini', encoding='utf-8')
        user_list = []
        for section in config.sections():
            user = {}
            for key, value in config[section].items():
                user[key] = value
            if user != {}:
                user_list.append(user)
        return user_list

    def set_cookie(self, account, password):
        """获取 cookie，后续操作通过 cookie 来识别学生身份"""
        url = 'https://student.hitsz.edu.cn/common/casLogin?params=L3hnX21vYmlsZS9ob21l'
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')  # 禁止沙箱模式，否则肯能会报错遇到chrome异常
        pref = {'profile.managed_default_content_settings.images': 2}  # 禁用图片加载
        options.add_experimental_option('prefs', pref)
        # 服务器使用
        # driver = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver', options=options)
        # 本地使用
        driver = webdriver.Chrome(options=options)

        driver.get(url)
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'form#fm1')))
        account_input = driver.find_element(by=By.ID, value='username')
        password_input = driver.find_element(by=By.ID,value='password')
        submit_button = driver.find_element(by=By.CLASS_NAME, value='login_box_landing_btn')
        account_input.send_keys(account)
        password_input.send_keys(password)
        submit_button.click()
        time.sleep(1)
        print(driver.page_source)
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.xg_qzzb_content')))

        # mrsb_button = driver.find_element(By.CSS_SELECTOR, 'div.part_action_left')
        # mrsb_button.click()
        # WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div#mask.daily_report_all')))


        cookies = driver.get_cookies()[-1]
        cookie = cookies['name'] + '=' + cookies['value']
        logging.info('Set cookie: ' + cookie)
        self.headers['Cookie'] = cookie
        driver.quit()

    def getToken(self):
        resp = requests.post("https://student.hitsz.edu.cn/xg_common/getToken", headers=self.headers)
        token = resp.text
        return token

    def checkTodayData(self):
        resp = requests.post("https://student.hitsz.edu.cn/xg_mobile/xsMrsbNew/checkTodayData", headers=self.headers)
        return resp.json()


    def getMrsb(self):
        resp = requests.post("https://student.hitsz.edu.cn/xg_mobile/xsMrsbNew/getMrsb", headers=self.headers)
        return resp.json()["module"]["data"][0]

    def save(self):
        keys = []
        saved_mrsb_data = {}
        mrsb_data = self.getMrsb()
        with open("data_keys.txt") as f:
            for line in f:
                keys.append(line.strip())
        for k in keys:
            saved_mrsb_data[k] = mrsb_data[k]
        data = {"info": json.dumps({"model": saved_mrsb_data, "token": self.getToken()})}
        resp = requests.post("https://student.hitsz.edu.cn/xg_mobile/xsMrsbNew/save", headers=self.headers, data=data)
        return resp.json()
    def post_new_info(self):
        try:
            resp = self.save()
            return resp["isSuccess"]
        except Exception as e:
            return False
    
    
    def run(self):
        user_list = self.get_user_list()
        for user in user_list:
            name = user['name']
            account = user['account']
            password = user['password']
            
            if account != '' and password != '':
                logging.info(f'当前上报用户：{name}')
                self.set_cookie(account, password)
                # try:
                if self.post_new_info() == True:
                    logging.info('上报结果：每日信息上报**成功**')
                else:
                    logging.info('上报结果：每日信息上报**失败**')
                # except Exception as e:
                #     logging.exception(e)
                #     logging.info('上报结果：每日信息上报**失败**')



if __name__ == '__main__':
    reporter = Reporter()
    reporter.run()