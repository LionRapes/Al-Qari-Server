import json
import os
import re
import sys


def apply_tajweed_phonetics(arabic_text):
    # 1. Handle Disconnected Letters (Huroof Muqatta'at)
    muqattaat = {
        "الٓمٓ": "Alif-Laaam-Meeem",
        "الٓمٓصٓ": "Alif-Laaam-Meeem-Saaad",
        "الٓر": "Alif-Laaam-Raa",
        "الٓمٓر": "Alif-Laaam-Meeem-Raa",
        "كٓهيٓعٓصٓ": "Kaaaf-Haa-Yaa-'Ayyyn-Saaad",
        "طه": "Taa-Haa",
        "طسٓمٓ": "Taa-Seeem-Meeem",
        "طسٓ": "Taa-Seeem",
        "يٓسٓ": "Yaa-Seeen",
        "صٓ": "Saaad",
        "حٓمٓ": "Haa-Meeem",
        "قٓ": "Qaaaf",
        "نٓ": "Nuun",
        "حٓمٓ عٓسٓقٓ": "Haa-Meeem 'Ayyyn-Seeen-Qaaaf",
    }

    clean_arabic = re.sub(r"[\u06D6-\u06DC\u06DF-\u06E8]", "", arabic_text).strip()
    if clean_arabic in muqattaat:
        return muqattaat[clean_arabic]

    # 2. Pre-process Uthmani Spelling Exceptions
    text = arabic_text
    text = text.replace("ٱلصَّلَوٰة", "ٱلصَّلَاة")  # Fix Salaah spelling
    text = text.replace("الصَّلَوٰة", "الصَّلَاة")
    text = text.replace("ٱلزَّكَوٰة", "ٱلزَّكَاة")  # Fix Zakaah spelling
    text = text.replace("الزَّكَوٰة", "الزَّكَاة")
    text = text.replace("أُوْلَٰٓئِكَ", "أُلَٰٓئِكَ")  # Remove silent waw in Ulaa'ika
    text = text.replace("مِاْئَة", "مِئَة")  # Remove silent alif in Mi'ata
    text = text.replace("واْ", "w")  # Remove silent alif in plural verbs
    text = text.replace("وا۟", "w")
    text = re.sub(r"[\u06D6-\u06DC\u06DF-\u06E8]", "", text)  # Strip waqf markers

    # 3. Base Character Mapping
    ARABIC_MAPPING = {
        "ا": "a",
        "ب": "b",
        "ت": "t",
        "ث": "th",
        "ج": "j",
        "ح": "h",
        "خ": "kh",
        "د": "d",
        "ذ": "z",
        "ر": "r",
        "ز": "z",
        "س": "s",
        "ش": "sh",
        "ص": "s",
        "ض": "d",
        "ط": "t",
        "ظ": "z",
        "ع": "'",
        "غ": "gh",
        "ف": "f",
        "ق": "q",
        "ك": "k",
        "ل": "l",
        "م": "m",
        "ن": "n",
        "ه": "h",
        "و": "w",
        "ي": "y",
        "ة": "t",
        "ى": "a",
        "ء": "'",
        "أ": "#",
        "إ": "#",
        "ؤ": "'",
        "ئ": "'",
        "ٱ": "@",
        "آ": "aa",  # '@' marks Alif Wasla, '#' marks Hamza
    }

    VOWELS = {
        "\u064e": "a",
        "\u0650": "i",
        "\u064f": "u",
        "\u064b": "an",
        "\u064d": "in",
        "\u064c": "un",
        "\u0670": "aa",
        "\u0653": "aa",
        "\u06e4": "aa",
    }

    SHADDA = "\u0651"

    raw = ""
    for char in text:
        if char in ARABIC_MAPPING:
            if char == "ة":
                raw += "t"
            else:
                raw += ARABIC_MAPPING[char]
        elif char in VOWELS:
            raw += VOWELS[char]
        elif char == SHADDA:
            # Double the last character if it is an alphabet letter
            if len(raw) > 0 and raw[-1].isalpha():
                if (
                    raw.endswith("sh")
                    or raw.endswith("th")
                    or raw.endswith("gh")
                    or raw.endswith("kh")
                ):
                    raw += raw[-2:]  # Double the digraph
                else:
                    raw += raw[-1]
        elif char == " ":
            raw += " "

    p = raw

    # 4. Clean up Hamzas and Connecting Alifs (Alif Wasla)
    p = re.sub(r"\b#", "", p)  # Drop word-initial Hamza
    p = p.replace("#", "'")  # Mid-word Hamza becomes apostrophe
    p = re.sub(r"([aiu])\s*@", r"\1", p)  # Drop Alif if preceded by vowel
    p = p.replace("@", "a")  # Otherwise, pronounce as 'A'

    # 5. Fix "Allah" formatting
    p = re.sub(r"l{3,}", "ll", p)  # Clean up triple 'l'
    p = p.replace("llah", "llaah")  # Add the hidden dagger alif

    # 6. Vowel Smoothing
    p = re.sub(r"a{3,}", "aa", p)
    p = p.replace("iy", "ee").replace("uw", "oo")
    p = p.replace("eeya", "iyya")
    p = p.replace("aay", "ay")

    # 7. Sun & Moon Letters (Assimilation)
    sun_letters = r"(t|th|d|z|r|s|sh|l|n)"
    # Assimilate Sun Letters (e.g. bi-s-salaati)
    p = re.sub(r"([aiu])l\s*" + sun_letters + r"\2", r"\1\2-\2", p, flags=re.IGNORECASE)
    p = re.sub(r"\ba?l\s*" + sun_letters + r"\1", r"a\1-\1", p, flags=re.IGNORECASE)
    # Connected Moon Letters (e.g. Rabbil 'aalameen)
    p = re.sub(r"([aiu])l(?=[a-z])", r"\1l ", p, flags=re.IGNORECASE)

    # 8. Idgham & Iqlab (Assimilation of Nun/Tanween)
    p = re.sub(r"(a|i|u)n\s+w", r"\1nw w", p, flags=re.IGNORECASE)
    p = re.sub(r"(a|i|u)n\s+y", r"\1ny y", p, flags=re.IGNORECASE)
    p = re.sub(r"(a|i|u)n\s+m", r"\1m m", p, flags=re.IGNORECASE)
    p = re.sub(r"(a|i|u)n\s+r", r"\1r r", p, flags=re.IGNORECASE)
    p = re.sub(r"(a|i|u)n\s+l", r"\1l l", p, flags=re.IGNORECASE)

    p = re.sub(r"\bn\s+m", "m m", p, flags=re.IGNORECASE)
    p = re.sub(r"\bn\s+r", "r r", p, flags=re.IGNORECASE)
    p = re.sub(r"\bn\s+l", "l l", p, flags=re.IGNORECASE)

    p = re.sub(r"(a|i|u)n\s+b", r"\1m b", p, flags=re.IGNORECASE)  # Iqlab
    p = re.sub(r"\bn\s+b", "m b", p, flags=re.IGNORECASE)

    # 9. Waqf (Stopping Rules)
    p = re.sub(r"(an|in|un|[aiu])$", "", p)  # Drop short vowels at the end
    p = re.sub(r"t$", "h", p)  # Convert trailing 't' to 'h'

    # Clean up
    p = p.replace("- ", " ")
    p = p.replace("--", "-")

    # 10. Capitalization
    if len(p) > 0:
        p = p[0].upper() + p[1:]

    return p


def upgrade_json_file(input_file, output_file):
    print(f"Loading Arabic JSON from {input_file}...")

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    upgraded_data = []

    for item in data:
        # Проверяем, есть ли поле 'verses' (новая структура) или 'ayats' (старая структура)
        if "verses" in item:
            # Новая структура с id, type, total_verses, verses
            print(f"Applying Russian Phonetics to: {item['name']}")

            new_item = {
                "id": item["id"],
                "name": apply_tajweed_phonetics(item["name"]),
                "verses": [],
            }

            for verse in item["verses"]:
                new_verse = {"id": verse["id"], "text": apply_tajweed_phonetics(verse["text"])}
                new_item["verses"].append(new_verse)

            upgraded_data.append(new_item)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(upgraded_data, f, ensure_ascii=False, indent=4)

    print(f"Success! Phonetic transliteration saved to {output_file}")


def process_all_files():
    input_dir = "riwaya"
    output_dir = "transcription"

    # Создаем папку для выходных файлов, если её нет
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Получаем все JSON файлы из папки riwaya
    json_files = [f for f in os.listdir(input_dir) if f.endswith(".json")]

    if not json_files:
        print("❌ В папке 'riwaya' нет JSON файлов!")
        return

    print(f"📁 Найдено файлов: {len(json_files)}")

    for file in json_files:
        input_path = os.path.join(input_dir, file)
        # Формируем имя выходного файла
        base_name = os.path.splitext(file)[0]  # Убираем расширение
        output_name = f"{base_name}_transcription_en.json"
        output_path = os.path.join(output_dir, output_name)

        upgrade_json_file(input_path, output_path)

    print(f"✅ Обработано {len(json_files)} файлов в папку '{output_dir}'")


def main():
    # Проверяем параметр 'all'
    if len(sys.argv) > 1 and sys.argv[1].lower() == "all":
        print("🚀 Режим: обработка всех файлов из папки 'riwaya'")
        process_all_files()
        return

    # Обычный режим с одним файлом
    if len(sys.argv) < 2:
        input_file = input("Print input file: ") or "hafs.json"
    else:
        input_file = sys.argv[1]

    if len(sys.argv) < 3:
        output_file = input("Print output file: ") or "hafs_transliteration_en.json"
    else:
        output_file = sys.argv[2]

    print(f"✅ Input: {input_file}")
    print(f"✅ Output: {output_file}")

    upgrade_json_file(input_file, output_file)


if __name__ == "__main__":
    main()
