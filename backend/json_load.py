import json
from recipes.models import Ingredient


def load_ingredients_from_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        for item in data:
            ingredient, created = Ingredient.objects.get_or_create(
                name=item['name'],
                defaults={'measurement_unit': item['measurement_unit']}
            )
            if not created:
                ingredient.measurement_unit = item['measurement_unit']
                ingredient.save()

        print('Данные успешно загружены')
    except FileNotFoundError:
        print(f'Файл {file_path} не найден')
    except json.JSONDecodeError:
        print('Ошибка декодирования JSON')
    except Exception as e:
        print(f'Произошла ошибка: {e}')
