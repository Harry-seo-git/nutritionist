import os
import csv
import random
import requests
from datetime import datetime
import pytz  # 시간대 처리를 위해 필요

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
CSV_URL = os.environ.get("CSV_URL")

if not SLACK_BOT_TOKEN or not CSV_URL:
    raise Exception("SLACK_BOT_TOKEN과 CSV_URL 환경 변수를 설정해주세요.")

def fetch_csv_data(url):
    response = requests.get(url)
    response.raise_for_status()
    decoded_content = response.content.decode('utf-8')
    reader = csv.DictReader(decoded_content.splitlines())
    data = list(reader)
    return data

def filter_data(data):
    filtered = []
    for row in data:
        try:
            rating = float(row.get("평점", "0"))
            if rating > 2:
                filtered.append(row)
        except ValueError:
            continue
    return filtered

def select_random_restaurants(data):
    count = random.randint(5, 6)
    return random.sample(data, count) if len(data) >= count else data

def get_formatted_date():
    tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(tz)
    weekday_map = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"}
    weekday = weekday_map[now.weekday()]
    formatted_date = f"{now.year}년 {now.month}월 {now.day}일({weekday})"
    return formatted_date

def build_slack_message(restaurants):
    header = f"*{get_formatted_date()}*"
    body_lines = [header, "\n오늘의 추천 맛집 목록입니다:\n"]
    
    for item in restaurants:
        line = (f"*{item.get('가게 이름', '이름없음')}* | {item.get('종류', '-')}"
                f" | 대표 메뉴: {item.get('대표 메뉴', '-')}"
                f" | 평점: {item.get('평점', '-')}"
                f" | 가격대: {item.get('가격대', '-')}"
                f" | 소요시간(거리): {item.get('소요시간(거리)', '-')}")
        body_lines.append(line)
        memo = item.get("메모", "")
        map_url = item.get("지도 URL", "")
        if memo:
            body_lines.append(f"> {memo}")
        if map_url:
            body_lines.append(f"{map_url}")
        body_lines.append("")
    
    fun_messages = [
        "자, 여러분! 이제 점심시간입니다. 오늘의 메뉴는 단순한 식사가 아니라, 감동을 선사할 요리의 예술입니다. 한 입 베어 물면 그 풍미에 감탄할 것입니다. 최고의 점심을 즐기세요! :fire:",
        "이제 점심입니다, 여러분! 오늘의 메뉴는 정성과 열정이 빚어낸 걸작입니다. 한 입 맛보면 요리의 진수를 느끼실 겁니다. 준비되셨나요? :chef:",
        "여러분, 점심 시간이 다가왔습니다. 오늘의 요리는 감탄을 자아내는 예술작품입니다. 한 입 베어 물면 여러분의 미각이 황홀경에 빠질 것입니다. 지금 바로 즐겨보세요! :sunglasses:"
    ]
    body_lines.append(random.choice(fun_messages))
    return "\n".join(body_lines)

# 봇이 초대된 채널 목록 조회 함수
def get_bot_channels():
    url = "https://slack.com/api/conversations.list"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json; charset=utf-8"
    }
    params = {
        "types": "public_channel,private_channel",
        "exclude_archived": "true"
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    if not data.get("ok"):
        raise Exception(f"채널 목록 조회 실패: {data}")
    # 봇이 멤버로 있는 채널만 필터링 (is_member: true)
    channels = [channel for channel in data.get("channels", []) if channel.get("is_member")]
    return channels

# 슬랙 메시지 전송 함수 (봇이 초대된 모든 채널에 전송)
def send_slack_message(message):
    channels = get_bot_channels()
    if not channels:
        raise Exception("봇이 초대된 채널이 없습니다.")
    
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json; charset=utf-8"
    }
    for channel in channels:
        payload = {
            "channel": channel["id"],
            "text": message,
        }
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()
        if not response_data.get("ok"):
            print(f"채널 {channel.get('name')}에 메시지 전송 실패: {response_data}")
        else:
            print(f"채널 {channel.get('name')}에 메시지 전송 성공")

if __name__ == "__main__":
    try:
        data = fetch_csv_data(CSV_URL)
        filtered = filter_data(data)
        selected = select_random_restaurants(filtered)
        slack_message = build_slack_message(selected)
        send_slack_message(slack_message)
    except Exception as e:
        print(f"오류 발생: {e}")
