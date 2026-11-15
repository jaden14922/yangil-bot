# 나이스에서 양일고 급식·시간표를 받아 data.json으로 저장한다.
# GitHub Actions가 매일 자동으로 실행한다. 인증키는 GitHub Secrets(NEIS_KEY)에서 읽는다.
# 사용법: python scripts/update.py 저장할경로/data.json

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

KEY = os.environ.get("NEIS_KEY", "").strip()
OFFICE_CODE = "J10"       # 경기도교육청
SCHOOL_CODE = "7530607"   # 양일고등학교
BASE_URL = "https://open.neis.go.kr/hub/"
KST = timezone(timedelta(hours=9))


def fetch_all(service, params):
    """여러 페이지에 걸친 결과를 모두 받아온다. 데이터가 없으면 빈 목록."""
    rows, page = [], 1
    while True:
        query = {
            "KEY": KEY, "Type": "json", "pIndex": page, "pSize": 1000,
            "ATPT_OFCDC_SC_CODE": OFFICE_CODE, "SD_SCHUL_CODE": SCHOOL_CODE,
        }
        query.update(params)
        url = BASE_URL + service + "?" + urllib.parse.urlencode(query)
        with urllib.request.urlopen(url, timeout=30) as res:
            data = json.loads(res.read().decode("utf-8"))

        if service not in data:
            result = data.get("RESULT", {})
            if result.get("CODE") == "INFO-200":   # 해당 데이터 없음
                break
            raise RuntimeError(f"나이스 오류 {result.get('CODE')}: {result.get('MESSAGE')}")

        total = data[service][0]["head"][0]["list_total_count"]
        rows += data[service][1]["row"]
        if len(rows) >= total:
            break
        page += 1
    return rows


def clean_dishes(text):
    """'김치볶음밥 (5.6.10.)<br/>계란국' → ['김치볶음밥', '계란국']"""
    dishes = []
    for item in text.split("<br/>"):
        item = re.sub(r"\([\d.\s]*\)", "", item).strip()
        if item:
            dishes.append(item)
    return dishes


def main():
    if not KEY:
        sys.exit("NEIS_KEY가 비어 있어요. GitHub 저장소 Settings → Secrets에 인증키를 넣어주세요.")
    out_path = sys.argv[1] if len(sys.argv) > 1 else "data.json"

    today = datetime.now(KST).date()
    fmt = lambda d: d.strftime("%Y%m%d")

    # 급식: 어제부터 2주 뒤까지
    meals = {}
    for r in fetch_all("mealServiceDietInfo", {
        "MLSV_FROM_YMD": fmt(today - timedelta(days=1)),
        "MLSV_TO_YMD": fmt(today + timedelta(days=13)),
    }):
        meals.setdefault(r["MLSV_YMD"], []).append({
            "type": r.get("MMEAL_SC_NM", ""),
            "kcal": r.get("CAL_INFO", ""),
            "dishes": clean_dishes(r.get("DDISH_NM", "")),
        })

    # 시간표: 이번 주 월요일부터 다음 주 금요일까지, 전 학년 전 반
    monday = today - timedelta(days=today.weekday())
    raw = {}
    for r in fetch_all("hisTimetable", {
        "TI_FROM_YMD": fmt(monday),
        "TI_TO_YMD": fmt(monday + timedelta(days=11)),
    }):
        cls = f'{int(r["GRADE"])}-{int(r["CLASS_NM"])}' if str(r.get("CLASS_NM", "")).isdigit() else f'{r["GRADE"]}-{r["CLASS_NM"]}'
        raw.setdefault(r["ALL_TI_YMD"], {}).setdefault(cls, {})[int(r["PERIO"])] = (r.get("ITRT_CNTNT") or "").lstrip("- ").strip()

    timetable, classes = {}, set()
    for day, by_class in raw.items():
        timetable[day] = {}
        for cls, periods in by_class.items():
            classes.add(cls)
            timetable[day][cls] = [[p, periods[p]] for p in sorted(periods)]

    def class_key(c):
        g, _, n = c.partition("-")
        return (int(g) if g.isdigit() else 99, int(n) if n.isdigit() else 99, c)

    data = {
        "updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "classes": sorted(classes, key=class_key),
        "meals": meals,
        "timetable": timetable,
    }
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"저장 완료: 급식 {len(meals)}일치, 시간표 {len(timetable)}일치, 반 {len(classes)}개")


if __name__ == "__main__":
    main()
