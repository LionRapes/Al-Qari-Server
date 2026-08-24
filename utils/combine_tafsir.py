import json
import os
import re
import sys


def combine_to_surah_format(input_dir, output_file):
    """
    Объединяет JSON файлы в формат:
    [
        {
            "id": 1,
            "verses": [
                {"id": 1, "text": "..."},
                {"id": 2, "text": "..."}
            ]
        }
    ]
    """
    # Получаем все JSON файлы из папки
    json_files = [f for f in os.listdir(input_dir) if f.endswith(".json")]

    # Сортируем по номеру суры (1.json, 2.json, ...)
    json_files.sort(
        key=lambda x: int(re.search(r"\d+", x).group()) if re.search(r"\d+", x) else 999
    )

    if not json_files:
        print(f"❌ В папке '{input_dir}' нет JSON файлов!")
        return

    print(f"📁 Найдено файлов: {len(json_files)}")

    combined_data = []

    for file in json_files:
        file_path = os.path.join(input_dir, file)
        print(f"📖 Читаем: {file}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Извлекаем номер суры из имени файла
            surah_id = int(re.search(r"\d+", file).group())

            # Создаем структуру для суры
            surah_data = {"id": surah_id, "verses": []}

            # Обрабатываем разные структуры
            if "ayahs" in data:
                # Структура как в 1.json (с ayahs)
                for ayah in data["ayahs"]:
                    surah_data["verses"].append(
                        {"id": ayah.get("ayah", 1), "text": ayah.get("text", "")}
                    )
            elif "verses" in data:
                # Структура как в en.json
                for verse in data["verses"]:
                    surah_data["verses"].append(
                        {"id": verse.get("id", 1), "text": verse.get("text", "")}
                    )
            elif isinstance(data, list):
                # Если файл - список аятов
                for idx, item in enumerate(data, 1):
                    if isinstance(item, dict):
                        surah_data["verses"].append(
                            {"id": item.get("id", idx), "text": item.get("text", "")}
                        )
                    else:
                        surah_data["verses"].append({"id": idx, "text": str(item)})
            elif isinstance(data, dict) and "text" in data:
                # Если файл - один аят
                surah_data["verses"].append({"id": 1, "text": data.get("text", "")})

            # Проверяем, есть ли аяты
            if surah_data["verses"]:
                # Сортируем аяты по id
                surah_data["verses"].sort(key=lambda x: x.get("id", 0))
                combined_data.append(surah_data)
            else:
                print(f"⚠️ В файле {file} нет аятов!")

        except json.JSONDecodeError as e:
            print(f"⚠️ Ошибка в файле {file}: {e}")
        except Exception as e:
            print(f"⚠️ Ошибка при чтении {file}: {e}")

    if not combined_data:
        print("❌ Не найдено данных для объединения!")
        return

    # Сортируем суры по id
    combined_data.sort(key=lambda x: x.get("id", 0))

    # Сохраняем результат
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Готово! Объединено {len(combined_data)} сур")
    total_verses = sum(len(surah["verses"]) for surah in combined_data)
    print(f"📊 Всего аятов: {total_verses}")
    print(f"📁 Сохранено в: {output_file}")

    return combined_data



def main():
    if len(sys.argv) < 2:
        input_dir = input("Введите путь к папке с JSON файлами: ").strip() or "."
    else:
        input_dir = sys.argv[1]

    if len(sys.argv) < 3:
        output_file = input("Введите имя выходного файла: ").strip() or "quran_combined.json"
    else:
        output_file = sys.argv[2]

    combine_to_surah_format(input_dir, output_file)

if __name__ == "__main__":
    main()
    
