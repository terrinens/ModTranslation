import asyncio
import copy
import json
import os.path
import sys

from tqdm.auto import tqdm
from os.path import join as opj

import translation.google_cloud.google_cloud as trg

# 중단 지점 기록 키 이름
recode_key_name = 'progress_line'


def role(txt):
    variable = ["%s", "(%s)", "%d"]
    unit = ["EU", "EU/t", "ppm", "mB", "EV", "EV/t", "*A"]
    color_code = ["§"]


def progress_line(origin_location, copy_location, debug=False) -> str:
    """
    :param origin_location: 원본 json의 위치를 요구합니다.
    :param copy_location: 복사본이 생성될 위치를 요구합니다.
    :param debug: 중단 지점 기록 값을 명시적으로 표현하고자 할 경우에 사용되는 값입니다.
    원본 복사본이 존재하지 않을 경우 복사 하며, 이미 존재 할 경우 번역 중단된 키를 리턴 합니다.
    """

    # 복사본 체크
    if not os.path.isfile(copy_location):
        print(f'KR 번역 파일이 존재하지 않습니다. {origin_location} 파일을 {copy_location} 이름으로 복사합니다.')

        with open(origin_location, 'r', encoding='UTF-8') as t:
            load = json.load(t)

        # 복사본 생성
        copy_json = copy.deepcopy(load)

        # 중단 지점 기록 키 생성
        zero_line_key = list(copy_json.keys())[0]
        copy_json[recode_key_name] = zero_line_key

        with open(copy_location, 'w', encoding='UTF-8') as t:
            json.dump(copy_json, t, ensure_ascii=False, indent=4)

        if debug: print(f'새 파일이 생성 되었으므로 {zero_line_key} 키부터 시작 가능 합니다.')

        return copy_json[recode_key_name]

    # 이미 존재할 경우 중단 지점 기록 값 반환
    else:
        with open(copy_location, 'r', encoding='UTF-8') as t:
            load = json.load(t)
            recode_key = load[recode_key_name]

        if debug: print(f'중단 지점을 발견 했습니다. {recode_key} 키부터 시작 가능 합니다.')

        return recode_key


def translate(origin_location, temp_location, complete_location):
    # 기록을 위한 함수
    def recode():
        with open(temp_location, 'w', encoding='UTF-8') as t:
            json.dump(data, t, ensure_ascii=False, indent=4)

    # 번역할 라인 번호. 오류 혹은 중단 포인트를 사용하기 위한 값이기도 합니다.
    progress_key = progress_line(origin_location, temp_location, True)

    with open(temp_location, 'r', encoding='UTF-8') as t:
        data = json.load(t)

    # 중단 지점까지 가기 위한 코드
    breaking_point = False
    # 진행 사항 표시를 위한 tqdm
    data_tqdm = tqdm(data)

    print(f'번역을 시작 합니다. 시작 키 위치는 {progress_key} 입니다.\n')
    
    try:
        for key in data_tqdm:
            if key == progress_key: breaking_point = True

            if breaking_point:
                # 기록, 번역할 텍스트
                progress_key, origin_txt = key, data[key]

                # 만약 텍스트 크기가 1 이하인 경우 오류가 발생 및 필요없는 비용이므로 무시 처리
                if len(origin_txt) < 1: continue

                options = dict(location="global", source_language_code='ru_ru', target_language_code='ko_kr')
                translation_txt = asyncio.run(trg.translate_text(origin_txt, option=options))

                # 기존 값에 번역값 덮어씌우기
                data[key] = translation_txt

    # 오류 발생시 번역을 중단하고, 중단된 지점을 기록합니다.
    except Exception as e:
        print(f"번역중 오류가 발생했습니다.\n중단 지점은 {progress_key} 입니다.\n")

        data[recode_key_name] = progress_key

        recode()
        print(e)
        sys.exit(0)

    except KeyboardInterrupt:
        print(f'번역중 중단 요청을 확인했습니다.\n중단 지점은 {progress_key} 입니다.')

        data[recode_key_name] = progress_key

        recode()
        sys.exit(0)
    finally:
        data_tqdm.close()

    print('번역이 완료 되었습니다.')
    del data[recode_key_name]

    print('번역된 파일을 기록중...')
    recode()
    os.rename(temp_location, f'{complete_location}')
    print(f'완료 되었습니다. 번역된 파일의 위치는 {complete_location} 입니다.')


if __name__ == '__main__':
    dir = 'GregTech Modern'

    origin_json = opj(dir, 'ru_ru.json')
    copy_name = opj(dir, 'temp_ko_kr.json')
    complete_name = opj(dir, 'ko_kr.json')

    translate(origin_json, copy_name, complete_name)
