import os
import time
import sqlite3
import traceback
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

LOGIN_URL = 'https://www.facebook.com/login.php?login_attempt=&lwv='
FACEBOOK_URL = "https://www.facebook.com/"

# 요소별 식별자
ID_name = 'fb-timeline-cover-name'
SELECTOR_psa = 'img.profilePic.img'  # 프로필 사진
SELECTOR_cover_picture = 'img.coverPhotoImg.photo.img'  # 커버 사진
CLASS_top_category = '_4qm1'  # 섹션 안에서 가장 큰 분류. 이 안에 <li>...</li>로 각 항목이 있다.
CLASS_top_category_name = '_h72 lfloat _ohe _50f8 _50f7'  # 가장 큰 분류의 분류명 텍스트
SELECTOR_content_with_page = '._50f5._50f7'  # 페이지가 있는 정보
CLASS_simple_information = 'fsl fwn fcg'  # 단순 텍스트 형태 정보
CLASS_major = '_50f7'  # 전공 (정확히 class="_50f7"인 엘리먼트)
ID_current_city = 'current_city'  # 현재 거주지
ID_hometown = 'hometown'  # 출신지
CLASS_other_places = '_43c8 _5f6p'  # 기타 살았던 곳
CLASS_mutiple_contact = 'uiList _4kg _6-h _704 _6-i'  # 복수개 등록할 수 있는 연락처 항목 내용


class FaceBook(object):
    def __init__(self):
        # self.input_crawl()
        self.cursor = sqlite3.connect('facebook.db').cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS fb (url TEXT, key TEXT, value TEXT)')
        self.spider_phantom()

    def __del__(self):
        self.cursor.close()
        self.cursor.connection.close()

    def input_crawl(self):
        # login
        driver = webdriver.Chrome()
        driver.get(LOGIN_URL)
        myemail = input("EMAIL: ")
        mypassword = input("PASSWORD: ")
        usr = driver.find_element_by_xpath("//input[@id='email']")
        password = driver.find_element_by_xpath("//input[@id='pass']")
        logbtn = driver.find_element_by_name('login')
        usr.send_keys(myemail)
        password.send_keys(mypassword)
        logbtn.click()
        time.sleep(3)

        # search the user who work at 한국정보기술연구원
        search_link = 'https://www.facebook.com/search/str/246914498727366/likers/intersect'
        driver.get(search_link)
        f = open('target.txt', 'w')
        i = 1
        print('search for input data...')
        scroll = driver.execute_script("return window.scrollY")
        while True:
            print(str(i) + ' scroll performed...')
            elemsCount = driver.execute_script(
                "return document.querySelectorAll('.stream-items > li.stream-item').length")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            scroll_temp = scroll
            scroll = driver.execute_script("return window.scrollY")
            print(scroll_temp)
            print(scroll)
            i += 1
            if scroll_temp == scroll:
                break
        print('scrolling done...')
        time.sleep(5)
        source = driver.page_source
        print('source lenght: '.format(len(source)))
        soup = BeautifulSoup(source, 'html.parser')
        elements = soup.find_all('div', attrs={'class': '_gll'})
        driver.close()

        # extract the href and convert the facebook address
        print('convert the facebook address...')
        for el in elements:
            try:
                id = el.find('a').attrs['href']
                if id.find('&') != -1:
                    id = id.split('&')[0]
                    id += '&sk=about&\n'
                else:
                    id = id.split('?')[0]
                    id += '/about?\n'
                f.write(id)
            except Exception as e:
                print(e)
                continue
        f.close()
        print('converting done...')

    def spider_phantom(self):
        # 1. 로그인하기
        # 페이지 로드
        driver = webdriver.PhantomJS()
        driver.get(LOGIN_URL)
        time.sleep(3)

        # 로그인
        my_email = input('login email: ')
        my_password = input('password: ')
        username_box = driver.find_element_by_xpath("//input[@id='email']")
        password_box = driver.find_element_by_xpath("//input[@id='pass']")
        login_botton = driver.find_element_by_name('login')
        username_box.send_keys(my_email)
        password_box.send_keys(my_password)
        login_botton.click()
        time.sleep(3)

        # 2. 개인 정보 가져오기
        with open('target.txt', 'r') as targets_file:  # 타겟 인물들의 section= 전까지의 url 파일 (줄바꿈으로 분리)
            targets = targets_file.read().splitlines()

        print(targets)
        # 각 타겟 인물에 대해 긁어오기
        for index, target_url in enumerate(targets, start=1):
            personal_data = dict()
            personal_data['url'] = [target_url]

            # 이 사람의 각 섹션 페이지에 대해 긁어오기
            try:
                # 경력 및 학력
                personal_data.update(self.grab_education(driver, target_url))
                # 거주했던 장소
                personal_data.update(self.grab_living(driver, target_url))
                # 연락처 및 기본 정보
                personal_data.update(self.grab_contact_info(driver, target_url))
                # 가족 및 결혼/연애 상태
                personal_data.update(self.grab_contact_relationship(driver, target_url))
            except:
                print('error:', target_url)
                traceback.print_exc()
                continue

            print('#{}'.format(index))
            for key, values in personal_data.items():
                print('{}: {}'.format(key, values))
                for value in values:
                    self.cursor.execute('INSERT INTO fb VALUES (?, ?, ?)', (personal_data['url'][0], key, value))
                    self.cursor.connection.commit()

            print()
        driver.close()

    def grab_education(self, driver, target_url):
        section = 'education'
        # print('--- SECTION: {} ---'.format(section))
        url = '{}section={}&pnref=about'.format(target_url, section)
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        result_data_of_section = dict()
        for top_category in soup.find_all(class_=CLASS_top_category):
            top_category_name = top_category.find(class_=CLASS_top_category_name).text
            # print(top_category_name)
            if top_category_name == '전문 기술':
                result_data_of_section['전문 기술'] = top_category.ul.text.split(' · ')
                continue

            content_list = []
            for content_li in top_category.ul.children:
                # 페이지 링크가 있는 내용 가져오기를 시도한다.
                content_element = content_li.select_one(SELECTOR_content_with_page)
                if content_element is None:
                    # 페이지 링크가 있는 정보 내용이 아닌 경우 - 텍스트 링크만 있는 내용 가져오기를 시도한다.
                    content_element = content_li.find(class_=CLASS_simple_information)
                    if content_element is None:
                        # 텍스트 링크만 있는 정보 내용도 아닌 경우 - 그냥 안의 텍스트를 가져온다.
                        content_element = content_li
                content = content_element.text
                if '정보 없음' in content or '정보 요청' in content:
                    continue

                # print('>', content)
                content_list.append(content)
            result_data_of_section[top_category_name] = content_list
        return result_data_of_section

    def grab_living(self, driver, target_url):
        section = 'living'
        # print('--- SECTION: {} ---'.format(section))
        url = '{}section={}&pnref=about'.format(target_url, section)
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        result_data_of_section = dict()

        current_city_li = soup.find(id=ID_current_city)
        if current_city_li is None:
            current_city = None
        else:
            current_city = current_city_li.a.text

        result_data_of_section = dict()
        result_data_of_section['현재 거주지'] = [current_city]
        # print('현재 거주지')
        # print('>', current_city)

        hometown_li = soup.find(id=ID_hometown)
        if hometown_li is not None:
            hometown = hometown_li.a.text
            result_data_of_section['출신지'] = [hometown]
            # print('출신지')
            # print('>', hometown)

        other_place_li_s = []
        other_place_li_s += soup.find_all(class_=CLASS_other_places)

        other_places = []
        # print('기타 살았던 곳')
        for place_li in other_place_li_s:
            place = place_li.a.text
            # print('>', place)
            other_places.append(place)

        result_data_of_section = dict()
        result_data_of_section['기타 살았던 곳'] = other_places

        return result_data_of_section

    def grab_contact_info(self, driver, target_url):
        section = 'contact-info'
        # print('--- SECTION: {} ---'.format(section))
        url = '{}section={}&pnref=about'.format(target_url, section)
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        result_data_of_section = dict()

        # 이름
        name = soup.find(id=ID_name).text
        result_data_of_section['이름'] = [name]

        # 사진
        psa = soup.select_one(SELECTOR_psa)
        if psa is not None:
            result_data_of_section['사진'] = [psa['src']]

        cover_picture = soup.select_one(SELECTOR_cover_picture)
        if cover_picture is not None:
            result_data_of_section['페이스북 커버 사진'] = [cover_picture['src']]

        # 연락처, 기타 정보
        for top_category in soup.find_all(class_=CLASS_top_category):
            for contact_li in top_category.ul.children:
                if '정보 없음' in contact_li.text:
                    continue
                contact_item = contact_li.div.find_all('div')
                contact_key = contact_item[0].text.strip()
                contact_value = contact_item[1]
                if '정보 요청' in contact_value.text:
                    continue

                if contact_key == '휴대폰':
                    # print('휴대폰')
                    mobile_numbers = []
                    for mobile_number_element in contact_value.find_all('li'):
                        mobile_number = mobile_number_element.text
                        # print('>', mobile_number)
                        mobile_numbers.append(mobile_number)

                    result_data_of_section['휴대폰'] = mobile_numbers

                elif contact_key == '기타 전화번호':
                    # print('기타 전화번호')
                    other_numbers = []
                    for other_number_li_s in contact_value.ul.children:
                        for number_li in other_number_li_s:
                            other_number = number_li.li.text
                            # print('>', other_number)
                            other_numbers.append(other_number)

                    result_data_of_section['기타 전화번호'] = other_numbers
                elif contact_key == '주소':
                    address_part_li_s = contact_value.ul.children
                    address = '\n'.join(map(lambda e: e.text, address_part_li_s))

                    result_data_of_section['주소'] = [address]
                    # print('주소')
                    # print('>', address)
                elif contact_key == '언어':
                    languages_text = contact_value.text

                    languages_list = languages_text.split(' · ')
                    result_data_of_section['언어'] = languages_list
                    # print('언어')
                    # print('>', languages_list)
                else:
                    # print(contact_key)
                    multiple_contact_ul = contact_value.find(class_=CLASS_mutiple_contact)
                    if multiple_contact_ul is None:
                        contact_text = contact_value.text
                        # print('>', contact_text)
                        result_data_of_section[contact_key] = [contact_text]
                    else:
                        contact_value_texts = list(map(lambda e: e.text, multiple_contact_ul.children))
                        # print('>', '> '.join(contact_value_texts))
                        result_data_of_section[contact_key] = contact_value_texts

        return result_data_of_section

    def grab_contact_relationship(self, driver, target_url):
        section = 'relationship'
        # print('--- SECTION: {} ---'.format(section))
        url = '{}section={}&pnref=about'.format(target_url, section)
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        result_data_of_section = dict()
        for top_category in soup.find_all(class_=CLASS_top_category):
            top_category_name = top_category.find(class_=CLASS_top_category_name).text
            # print(top_category_name)

            content_list = []
            for content_li in top_category.ul.children:
                # 페이지 링크가 있는 내용 가져오기를 시도한다.
                content_element = content_li.select_one(SELECTOR_content_with_page)
                if content_element is None:
                    # 페이지 링크가 있는 정보 내용이 아닌 경우 - 텍스트 링크만 있는 내용 가져오기를 시도한다.
                    content_element = content_li.find(class_=CLASS_simple_information)
                    if content_element is None:
                        # 텍스트 링크만 있는 정보 내용도 아닌 경우 - 그냥 안의 텍스트를 가져온다.
                        content_element = content_li
                content = content_element.text
                if '없음' in content:
                    continue

                # print('>', content)
                content_list.append(content)

            result_data_of_section[top_category_name] = content_list
        return result_data_of_section


if __name__ == '__main__':
    if os.path.exists('facebook.db'):
        os.unlink('facebook.db')
    fb = FaceBook()
