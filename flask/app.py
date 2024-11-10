from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
from lxml import html
import pandas as pd
from datetime import datetime
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 모든 도메인에서 접근 가능하게 설정

@app.route('/scrape', methods=['GET'])
def scrape_data():
    try:
        # 웹 드라이버 초기화 및 페이지 열기
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get("https://dbbank.kovo.co.kr/login.asp")

        # 로그인 정보 입력 (사용자가 제공하는 값으로 수정 가능)
        username = "your_username"
        password = "your_password"  # 비밀번호를 입력하세요

        driver.find_element(By.NAME, "id").send_keys(username)
        driver.find_element(By.NAME, "pw").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit' and contains(text(), '로그인')]").click()

        time.sleep(2)
        driver.find_element(By.XPATH, "//span[@class='txt' and contains(text(), '이전 일자')]").click()
        time.sleep(2)
        v2_button = driver.find_element(By.XPATH, "//li[contains(@class, 'left on man')]//span[contains(text(), '(V2)')]")
        v2_button.click()

        time.sleep(3)

        # 새 창으로 전환
        new_window_handle = driver.window_handles[-1]
        driver.switch_to.window(new_window_handle)

        # 페이지 HTML 가져오기
        html_content = driver.page_source
        tree = html.fromstring(html_content)

        date_text = tree.xpath("//h3[@class='date']/text()")
        if date_text:
            date_str = date_text[0].strip().split(' ')[0]
            try:
                date_obj = datetime.strptime(date_str, "%Y.%m.%d")
                formatted_date = date_obj.strftime("%Y%m%d")
            except ValueError:
                formatted_date = datetime.now().strftime("%Y%m%d")
        else:
            formatted_date = datetime.now().strftime("%Y%m%d")

        # 첫 번째 테이블 데이터 추출
        caption_text = "선수 기록 안내 표로 PLAYER, Set, Pts, 공격종합, 오픈, 속공, 퀵오픈, 시간차, 이동, 후위, 블로킹, BA, 서브, 세트, 리시브, 디그, 벌칙, 범실, Exc 으로 구성"
        table_1 = tree.xpath(f"//table[caption[text()='{caption_text}']]")
        data_1 = []
        if table_1:
            data_rows_1 = table_1[0].xpath(".//tr[td and not(ancestor::tfoot)]")
            for row in data_rows_1:
                cols = row.xpath(".//td")
                cleaned_cols = [col.text_content().strip() if col.text_content().strip() else None for col in cols]
                if cleaned_cols:
                    data_1.append(cleaned_cols)

        # 두 번째 테이블 데이터 추출
        current_li = driver.find_element(By.XPATH, "//div[@class='wrp_tab type2']//li[@class='on']")
        next_li = current_li.find_element(By.XPATH, "following-sibling::li")
        next_li.click()

        time.sleep(3)
        html_content = driver.page_source
        tree = html.fromstring(html_content)

        table_2 = tree.xpath(f"//table[caption[text()='{caption_text}']]")
        data_2 = []
        if table_2:
            data_rows_2 = table_2[0].xpath(".//tr[td and not(ancestor::tfoot)]")
            for row in data_rows_2:
                cols = row.xpath(".//td")
                cleaned_cols = [col.text_content().strip() if col.text_content().strip() else None for col in cols]
                if cleaned_cols:
                    data_2.append(cleaned_cols)

        if data_1 and data_2:
            combined_df = pd.concat([pd.DataFrame(data_1), pd.DataFrame(data_2)], ignore_index=True)
            combined_df = combined_df.drop(combined_df.columns[0], axis=1)
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "24-25", "데이터_남자")
            if not os.path.exists(desktop_path):
                os.makedirs(desktop_path)
            file_path = os.path.join(desktop_path, f"m_{formatted_date}.xlsx")
            combined_df.to_excel(file_path, index=False)

            return jsonify({"message": "Scraping successful", "file": file_path}), 200

        else:
            return jsonify({"message": "No data found"}), 404

    except Exception as e:
        return jsonify({"message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
