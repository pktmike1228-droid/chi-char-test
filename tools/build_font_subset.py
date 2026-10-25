"""產生全字庫正楷體（TW-Kai）的網頁字型子集。

只保留網站實際用到的字，讓手機也能快速載入標準楷書：
  - data.csv 裡的所有文字（生字、詞語、部首、課名、注音）
  - index.html 裡的所有文字
  - 完整注音符號、聲調符號、〇、數字與常用標點

用法：
  python3 tools/build_font_subset.py <TW-Kai-98_1.ttf 路徑>

輸出：fonts/tw-kai-subset.woff2
字型授權：全字庫正楷體由國家發展委員會提供，採政府資料開放授權條款第 1 版
（https://data.gov.tw/license），亦可選擇 SIL Open Font License 1.1。
"""
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "fonts" / "tw-kai-subset.woff2"


def collect_text() -> set[str]:
    chars: set[str] = set()
    for name in ("data.csv", "index.html"):
        chars.update((ROOT / name).read_text(encoding="utf-8-sig"))
    # 注音符號 ㄅ～ㄩ 與聲調符號：ˊ ˇ ˋ ˙
    chars.update(chr(c) for c in range(0x3105, 0x312A))
    chars.update("ˊˇˋ˙〇")
    # 數字、英文與常用標點
    chars.update(chr(c) for c in range(0x20, 0x7F))
    chars.update("，。、：；？！「」『』（）《》〈〉…—．·【】")
    # 排除控制字元與換行
    return {c for c in chars if c.isprintable() and c not in "\r\n\t"}


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("用法：python3 tools/build_font_subset.py <TW-Kai-98_1.ttf 路徑>")
    source = Path(sys.argv[1])
    text = collect_text()

    cmap = TTFont(source, lazy=True).getBestCmap()
    # 只檢查中文字與注音（表情符號等本來就不在楷體字型內）
    missing = sorted(c for c in text if 0x2E80 <= ord(c) <= 0x9FFF and ord(c) not in cmap)

    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["*"]
    options.hinting = False
    options.name_IDs = ["*"]
    options.name_legacy = True
    options.name_languages = ["*"]

    font = subset.load_font(str(source), options)
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=[ord(c) for c in text])
    subsetter.subset(font)

    OUTPUT.parent.mkdir(exist_ok=True)
    subset.save_font(font, str(OUTPUT), options)

    size_kb = OUTPUT.stat().st_size / 1024
    print(f"已輸出 {OUTPUT.relative_to(ROOT)}：{len(text)} 個字元，{size_kb:.0f} KB")
    if missing:
        # 只警告不中斷：缺的字會由備援字型顯示
        print("警告：以下中文字不在此字型檔內，會改用備援字型顯示：" + "".join(missing))


if __name__ == "__main__":
    main()
