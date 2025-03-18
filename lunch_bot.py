import os
import random
import pandas as pd
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime

# Slack 토큰 설정
SLACK_TOKEN = os.environ['SLACK_TOKEN']
client = WebClient(token=SLACK_TOKEN)

# CSV 파일 URL
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTwC1Tqy70h0D_Rl4EkEl-Zq1p1YIRBi9blfebs2J7HnxC8X6S-l4b8LDTwxC80aKHAhQ8Dv5eKtg5m/pub?output=csv"

def get_lunch_recommendations():
    # CSV 파일 읽기
    df = pd.read_csv(CSV_URL)
    
    # 평점이 2 초과인 항목만 필터링
    df_filtered = df[df['평점'] > 2]
    
    # 무작위로 5~6곳 선택
    recommendations = df_filtered.sample(n=random.randint(5, 6))
    
    return recommendations

def format_message(recommendations):
    today = datetime.now().strftime("%Y년 %m월 %d일(%a)")
    
    message = f"*{today}*\n\n"
    
    intros = [
        "자, 여러분! 이제 점심시간입니다. 오늘의 메뉴는 단순한 식사가 아니라, 감동을 선사할 요리의 예술입니다. 한 입 베어 물면 그 풍미에 감탄할 것입니다. 최고의 점심을 즐기세요! :fire:",
        "이제 점심입니다, 여러분! 오늘의 메뉴는 정성과 열정이 빚어낸 걸작입니다. 한 입 맛보면 요리의 진수를 느끼실 겁니다. 준비되셨나요? :chef:",
        "여러분, 점심 시간이 다가왔습니다. 오늘의 요리는 감탄을 자아내는 예술작품입니다. 한 입 베어 물면 여러분의 미각이 황홀경에 빠질 것입니다. 지금 바로 즐겨보세요! :sunglasses:"
    ]
    
    message += random.choice(intros) + "\n\n"
    
    for _, row in recommendations.iterrows():
        message += f"*{row['가게 이름']}* ({row['종류']})\n"
        message += f"• 대표 메뉴: {row['대표 메뉴']}\n"
        message += f"• 평점: {row['평점']}\n"
        message += f"• 가격대: {row['가격대']}\n"
        message += f"• 소요시간: {row['소요시간(거리)']}\n"
        message += f"• 메모: {row['메모']}\n"
        message += f"• 지도: {row['지도 URL']}\n\n"
    
    return message

def send_message(channel_id, message):
    try:
        result = client.chat_postMessage(
            channel=channel_id,
            text=message
        )
        print(f"Message sent to channel {channel_id}")
    except SlackApiError as e:
        print(f"Error sending message: {e}")

def main():
    recommendations = get_lunch_recommendations()
    message = format_message(recommendations)
    
    # 봇이 초대된 모든 채널에 메시지 전송
    try:
        result = client.conversations_list()
        for channel in result["channels"]:
            if channel["is_member"]:
                send_message(channel["id"], message)
    except SlackApiError as e:
        print(f"Error listing conversations: {e}")

if __name__ == "__main__":
    main()
