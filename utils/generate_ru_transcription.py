import json
import os
import re
import sys


def apply_tajweed_phonetics(arabic_text):
    # 1. Handle Disconnected Letters (Huroof Muqatta'at)
    muqattaat = {
        "الٓمٓ": "Алиф-Ляям-Миим",
        "الٓمٓصٓ": "Алиф-Ляям-Миим-Саад",
        "الٓر": "Алиф-Ляям-Ра",
        "الٓمٓر": "Алиф-Ляям-Миим-Ра",
        "كٓهيٓعٓصٓ": "Кааф-Ха-Йа-'Аййн-Саад",
        "طه": "Та-Ха",
        "طسٓمٓ": "Та-Сиим-Миим",
        "طسٓ": "Та-Сиим",
        "يٓسٓ": "Йа-Сиин",
        "صٓ": "Саад",
        "حٓمٓ": "Ха-Миим",
        "قٓ": "Кааф",
        "نٓ": "Нуун",
        "حٓمٓ عٓسٓقٓ": "Ха-Миим 'Аййн-Сиин-Кааф",
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
    text = text.replace("أُوْلَٰٓئِكَ", "أُلَٰٓئِكَ")  # Remove silent waw
    text = text.replace("مِاْئَة", "مِئَة")  # Remove silent alif
    text = text.replace("واْ", "w")  # Remove silent alif in plural verbs
    text = text.replace("وا۟", "w")
    text = re.sub(r"[\u06D6-\u06DC\u06DF-\u06E8]", "", text)  # Strip waqf markers

    # 3. Base Character Mapping to Cyrillic
    ARABIC_MAPPING = {
        "ا": "а",
        "ب": "б",
        "ت": "т",
        "ث": "с",
        "ج": "дж",
        "ح": "х",
        "خ": "х",
        "د": "д",
        "ذ": "з",
        "ر": "р",
        "ز": "з",
        "س": "с",
        "ش": "ш",
        "ص": "с",
        "ض": "д",
        "ط": "т",
        "ظ": "з",
        "ع": "'",
        "غ": "г",
        "ف": "ф",
        "ق": "к",
        "ك": "к",
        "ل": "л",
        "م": "м",
        "н": "н",
        "ه": "х",
        "و": "в",
        "ي": "й",
        "ة": "Т",
        "ى": "а",
        "ء": "'",
        "أ": "#",
        "إ": "#",
        "ؤ": "'",
        "ئ": "'",
        "ٱ": "@",
        "آ": "аа",  # '@' marks Alif Wasla, '#' marks Hamza, 'Т' marks Ta Marbuta
    }

    # Map Standard and Sequential (Tajweed) Vowels
    VOWELS = {
        "\u064e": "а",
        "\u0650": "и",
        "\u064f": "у",
        "ً": "ан",
        "ٍ": "ин",
        "ٌ": "ун",  # Standard Tanween
        "ٗ": "ан",
        "ٖ": "ин",
        "ٞ": "ун",  # Sequential Tanween used in Quran
        "\u0670": "аа",
        "\u0653": "аа",
        "\u06e4": "аа",
    }

    SHADDA = "\u0651"

    raw = ""
    for char in text:
        if char in ARABIC_MAPPING:
            raw += ARABIC_MAPPING[char]
        elif char in VOWELS:
            raw += VOWELS[char]
        elif char == SHADDA:
            if len(raw) > 0 and re.match(r"[а-яё\']", raw[-1], re.IGNORECASE):
                if raw.endswith("дж"):
                    raw += "дж"
                else:
                    raw += raw[-1]
        elif char == " ":
            raw += " "

    p = raw

    # 4. Clean up Hamzas and Connecting Alifs (Alif Wasla)
    p = re.sub(r"\b#", "", p)  # Drop word-initial Hamza
    p = p.replace("#", "")  # Mid-word Hamza is dropped for smooth Russian reading
    p = re.sub(r"([аиу])\s*@", r"\1", p)  # Drop Alif Wasla if preceded by vowel
    p = p.replace("@", "а")  # Otherwise, pronounce as 'а'

    # 5. Fix "Allah" formatting
    p = re.sub(r"л{3,}", "лл", p)
    p = p.replace("ллах", "ллаах")

    # 6. Vowel Smoothing for Cyrillic Phonetics
    p = re.sub(r"а{3,}", "аа", p)
    p = p.replace("иййа", "иййа")
    p = re.sub(r"ув(?=[^аиу]|$)", "уу", p)  # e.g. Damma + Waw = 'уу'
    p = re.sub(r"ий+", "ий", p)  # e.g. Kasra + Yaa = 'ий'

    # 7. Sun & Moon Letters (Assimilation)
    sun_letters = r"(т|с|д|з|р|ш|л|н|Т)"
    # Assimilate Sun Letters (e.g. а лссираата -> ас-сираата)
    p = re.sub(r"([аиу])л\s*(" + sun_letters + r")\2", r"\1\2-\2", p, flags=re.IGNORECASE)
    p = re.sub(r"\bа?л\s*(" + sun_letters + r")\1", r"а\2-\2", p, flags=re.IGNORECASE)
    # Connect Moon Letters (e.g. рабби л'ааламийн)
    p = re.sub(r"([аиу])л\s*(?=[а-яё\'])", r"\1л ", p, flags=re.IGNORECASE)

    # 8. Idgham & Iqlab (Assimilation of Nun/Tanween)
    p = re.sub(r"(а|и|у)н\s+в", r"\1нв в", p, flags=re.IGNORECASE)
    p = re.sub(r"(а|и|у)н\s+й", r"\1нй й", p, flags=re.IGNORECASE)
    p = re.sub(r"(а|и|у)н\s+м", r"\1м м", p, flags=re.IGNORECASE)
    p = re.sub(r"(а|и|у)н\s+р", r"\1р р", p, flags=re.IGNORECASE)
    p = re.sub(r"(а|и|у)н\s+л", r"\1л л", p, flags=re.IGNORECASE)

    p = re.sub(r"\bн\s+м", "м м", p, flags=re.IGNORECASE)
    p = re.sub(r"\bн\s+р", "р р", p, flags=re.IGNORECASE)
    p = re.sub(r"\bн\s+л", "л л", p, flags=re.IGNORECASE)

    p = re.sub(r"(а|и|у)н\s+б", r"\1м б", p, flags=re.IGNORECASE)  # Iqlab
    p = re.sub(r"\bн\s+б", "м б", p, flags=re.IGNORECASE)

    # 9. Waqf (Stopping Rules)
    p = re.sub(r"Тан$", "х", p)  # Ta Marbuta + Fathatan stops as 'х'
    p = re.sub(r"Т(ин|ун|[аиу])$", "х", p)  # Ta Marbuta stops as 'х'
    p = re.sub(r"Т$", "х", p)
    p = re.sub(r"ан$", "аа", p)  # Normal Fathatan stops as 'аа' (Madd 'Iwad)
    p = re.sub(r"(ин|ун|[аиу])$", "", p)  # Drop short vowels at the end

    # 10. Clean up artifacts & Ta Marbuta mid-sentence
    p = p.replace("Т", "т")
    p = p.replace("- ", " ")
    p = p.replace("--", "-")

    # Capitalize
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

    print(f"Success! Russian Phonetic transliteration saved to {output_file}")


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
        output_name = f"{base_name}_transcription_ru.json"
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
        output_file = input("Print output file: ") or "hafs_transliteration_ru.json"
    else:
        output_file = sys.argv[2]

    print(f"✅ Input: {input_file}")
    print(f"✅ Output: {output_file}")

    upgrade_json_file(input_file, output_file)


if __name__ == "__main__":
    main()
