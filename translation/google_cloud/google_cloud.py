# Google Cloud 번역 라이브러리를 가져옵니다.
import json
import os
from os.path import join as opj

from google.cloud import translate

drive_path = os.path.abspath(__file__)
this_path = os.path.dirname(drive_path)
oauth_key = opj(this_path, 'key/google_cloud_key.json')

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = oauth_key

# key.json에서 프로젝트 ID 가져오기
with open(oauth_key, "r") as j:
    data = json.load(j)

# 프로젝트 ID
project_id = data["project_id"]


# 번역 함수
# noinspection PyDefaultArgument
async def translate_text(
        text: str = "YOUR_TEXT_TO_TRANSLATE",
        option: dict = dict(location="global", source_language_code="en-US", target_language_code="ko")
) -> str:
    # key 값 인증
    client = translate.TranslationServiceClient()

    location = option.get('location')
    parent = f"projects/{project_id}/locations/{location}"

    # 텍스트를 영어에서 한국어로 번역하세요
    response = client.translate_text(
        request={
            "parent": parent,
            "contents": [text],
            "mime_type": "text/plain",  # mime types: text/plain, text/html
            "source_language_code": option.get('source_language_code'),
            "target_language_code": option.get('target_language_code'),
        }
    )

    # 제공된 각 입력 텍스트에 대한 번역을 표시합니다.
    for translation in response.translations:
        print(f"번역 전 텍스트 : {text}")
        print(f"번역 후 텍스트 : {translation.translated_text}\n")

        return translation.translated_text


if __name__ == '__main__':
    translate_text("hello world")
