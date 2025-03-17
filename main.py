import os
import csv
import requests
import random
from datetime import datetime
import pytz

# 1. CSV 데이터 URL (구글 스프레드시트의 공개 CSV 링크)
CSV_URL = "https://docs.google.com/spreadsheets/d/your_sheet_id/export?format=csv"  # 본인의 CSV 링크로 교체하세요

# 2. Slack API URL
SLACK_API_URL = "https://slack.com/api/chat.postMessage"

def fetch_and_parse_csv(url):
    response = requests.get(url)
    response.encoding = 'utf-8'
    decoded_content = response.text.splitlines()
    reader = csv.DictReader(decoded_content)
    data = list(reader)
    return data

def filter_restaurants(data):
    filtered = []
    for row in data:
        try:
            rating = float(row['평점'])
        except ValueError:
            continue
        if rating > 2:
            filtered.append(row)
    return filtered

def select_random_restaurants(data):
    count = random.choice([5, 6])
    if len(data) < count:
        count = len(data)
    return random.sample(data, count)

def format_date_kst():
    tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(tz)
    # 요일 표시: 0=월, 1=화, ... 6=일
    day_names = ['월', '화', '수', '목', '금', '토', '일']
    formatted_date = now.strftime(f"%Y년 %m월 %d일({day_names[now.weekday()]})")
    return formatted_date

def get_random_cheerful_message():
    messages = [
        "자, 여러분! 이제 점심시간입니다. 오늘의 메뉴는 단순한 식사가 아니라, 감동을 선사할 요리의 예술입니다. 한 입 베어 물면 그 풍미에 감탄할 것입니다. 최고의 점심을 즐기세요! :fire:",
        "이제 점심입니다, 여러분! 오늘의 메뉴는 정성과 열정이 빚어낸 걸작입니다. 한 입 맛보면 요리의 진수를 느끼실 겁니다. 준비되셨나요? :chef:",
        "여러분, 점심 시간이 다가왔습니다. 오늘의 요리는 감탄을 자아내는 예술작품입니다. 한 입 베어 물면 여러분의 미각이 황홀경에 빠질 것입니다. 지금 바로 즐겨보세요! :sunglasses:"
    ]
    return random.choice(messages)

def compose_message(restaurants):
    header = f"*{format_date_kst()} 점심 추천 메뉴*"
    body = ""
    for r in restaurants:
        # 맛집 정보 출력: 가게 이름, 종류, 대표 메뉴, 평점, 가격대, 소요시간(거리)
        body += f"\n*{r['가게 이름']}* ({r['종류']}) - 대표 메뉴: {r['대표 메뉴']}, 평점: {r['평점']}, 가격대: {r['가격대']}, 소요시간(거리): {r['소요시간(거리)']}\n"
        body += f"_{r['메모']}_\n"
        body += f"<{r['지도 URL']}|지도보기>\n"
    cheerful_message = get_random_cheerful_message()
    full_message = f"{header}\n{body}\n{cheerful_message}"
    return full_message

def send_slack_message(message, channel, token):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "channel": channel,
        "text": message
    }
    response = requests.post(SLACK_API_URL, headers=headers, json=data)
    return response.json()

def main():
    # 환경 변수에서 Slack 토큰과 채널 ID 읽기
    slack_token = os.environ.get("SLACK_BOT_TOKEN")
    slack_channel = os.environ.get("SLACK_CHANNEL")
    if not slack_token or not slack_channel:
        print("Slack 토큰이나 채널 ID가 설정되지 않았습니다.")
        return

    data = fetch_and_parse_csv(CSV_URL)
    filtered = filter_restaurants(data)
    if not filtered:
        print("조건에 맞는 맛집 데이터가 없습니다.")
        return

    selected = select_random_restaurants(filtered)
    message = compose_message(selected)
    result = send_slack_message(message, slack_channel, slack_token)
    print(result)

if __name__ == "__main__":
    main()
