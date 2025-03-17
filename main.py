import os
import csv
import random
import requests
from datetime import datetime
import pytz  # 시간대 처리를 위해 설치 (requirements.txt에 추가)

# 환경 변수에서 Slack Token과 CSV URL 읽기
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
CSV_URL = os.environ.get("CSV_URL")

if not SLACK_BOT_TOKEN or not CSV_URL:
    raise Exception("SLACK_BOT_TOKEN과 CSV_URL 환경 변수를 설정해주세요.")

# 1. CSV 데이터 가져오기
def fetch_csv_data(url):
    response = requests.get(url)
    response.raise_for_status()
    decoded_content = response.content.decode('utf-8')
    reader = csv.DictReader(decoded_content.splitlines())
    data = list(reader)
    return data

# 2. 평점이 2 초과인 항목 필터링
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

# 3. 무작위로 5~6개 항목 선택
def select_random_restaurants(data):
    count = random.randint(5, 6)
    return random.sample(data, count) if len(data) >= count else data

# 4. 오늘 날짜를 한국 형식으로 포맷하기 (예: 2025년 1월 1일(월))
def get_formatted_date():
    # 한국 시간(KST)으로 변환
    tz = pytz.timezone('Asia/Seoul')
    now = datetime.now(tz)
    weekday_map = {
        0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"
    }
    weekday = weekday_map[now.weekday()]
    formatted_date = f"{now.year}년 {now.month}월 {now.day}일({weekday})"
    return formatted_date

# 5. 슬랙 메시지 작성
def build_slack_message(restaurants):
    header = f"*{get_formatted_date()}*"
    body_lines = [header, "\n오늘의 추천 맛집 목록입니다:\n"]
    
    for item in restaurants:
        # 각 항목 출력: 가게 이름, 종류, 대표 메뉴, 평점, 가격대, 소요시간(거리)
        line = (f"*{item.get('가게 이름', '이름없음')}* | {item.get('종류', '-')}"
                f" | 대표 메뉴: {item.get('대표 메뉴', '-')}"
                f" | 평점: {item.get('평점', '-')}"
                f" | 가격대: {item.get('가격대', '-')}"
                f" | 소요시간(거리): {item.get('소요시간(거리)', '-')}")
        body_lines.append(line)
        # 메모와 지도 URL (메모 밑에 표시)
        memo = item.get("메모", "")
        map_url = item.get("지도 URL", "")
        if memo:
            body_lines.append(f"> {memo}")
        if map_url:
            body_lines.append(f"{map_url}")
        body_lines.append("")  # 항목 사이에 공백 줄 추가

    # 유쾌한 멘트 랜덤 선택
    fun_messages = [
        "자, 여러분! 이제 점심시간입니다. 오늘의 메뉴는 단순한 식사가 아니라, 감동을 선사할 요리의 예술입니다. 한 입 베어 물면 그 풍미에 감탄할 것입니다. 최고의 점심을 즐기세요! :fire:",
        "이제 점심입니다, 여러분! 오늘의 메뉴는 정성과 열정이 빚어낸 걸작입니다. 한 입 맛보면 요리의 진수를 느끼실 겁니다. 준비되셨나요? :chef:",
        "여러분, 점심 시간이 다가왔습니다. 오늘의 요리는 감탄을 자아내는 예술작품입니다. 한 입 베어 물면 여러분의 미각이 황홀경에 빠질 것입니다. 지금 바로 즐겨보세요! :sunglasses:"
    ]
    body_lines.append(random.choice(fun_messages))
    return "\n".join(body_lines)

# 6. 슬랙 메시지 전송
def send_slack_message(message):
    url = "https://slack.com/api/chat.postMessage"
    headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
    payload = {
        "text": message,
        # 채널은 봇이 이미 초대된 채널이면 생략해도 되며, 특정 채널을 지정하려면 "channel": "#channel-name" 등을 추가
    }
    response = requests.post(url, headers=headers, json=payload)
    response_data = response.json()
    if not response_data.get("ok"):
        raise Exception(f"Slack 메시지 전송 실패: {response_data}")
    print("Slack 메시지 전송 성공")

if __name__ == "__main__":
    try:
        # CSV 데이터를 가져와서 처리
        data = fetch_csv_data(CSV_URL)
        filtered = filter_data(data)
        selected = select_random_restaurants(filtered)
        
        # 슬랙 메시지 생성
        slack_message = build_slack_message(selected)
        
        # 슬랙 메시지 전송
        send_slack_message(slack_message)
    except Exception as e:
        print(f"오류 발생: {e}")
