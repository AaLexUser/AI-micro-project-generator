from bs4 import BeautifulSoup
import re

def extract_full_code_and_comments(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []

    # Находим все файлы 
    for file_div in soup.find_all('div', class_='source-tree__file'):
        # Извлекаем имя файла
        file_name_tag = file_div.find('span', class_='source-tree__file-name')
        if not file_name_tag:
            continue
        file_name = file_name_tag.get_text(strip=True)

        # Собираем полный код файла 
        code_lines = []
        code_elements = file_div.find_all('div', class_='source-tree__code-line')

        for line_elem in code_elements:
            code_block = line_elem.find('code', class_='source-tree__code-block')
            if not code_block:
                continue

            # Извлекаем текст с сохранением пробелов
            parts = []
            for child in code_block.children:
                if child.name == 'span':
                    parts.append(child.get_text())
                elif child.name is None:
                    parts.append(str(child))
            line_text = ''.join(parts)
            line_text = re.sub(r'\s+', ' ', line_text).strip()
            code_lines.append(line_text)

        full_code = '\n'.join(code_lines)

        # Находим все ошибки в этом файле
        for line_elem in code_elements:
            
            # Ищем оранжевую подсветку
            highlight = line_elem.find('div', class_='source-tree__line-highlight_critical')
            if not highlight:
                continue

            # Извлекаем номер строки
            line_number_elem = line_elem.find('div', class_='source-tree__line-number')
            if not line_number_elem:
                continue
            try:
                line_number = int(line_number_elem.get_text(strip=True))
            except:
                continue

            # Ищем комментарий
            comment_wrapper = line_elem.find('div', class_='source-tree__line-comment-wrapper')
            if not comment_wrapper:
                continue

            status_span = comment_wrapper.find('span', class_='source-tree__comment-info-status_type_critical')
            if not status_span or 'Надо исправить' not in status_span.get_text():
                continue

            # Извлекаем текст комментария
            paragraphs = comment_wrapper.find_all('div', class_='paragraph')
            comment_text = ' '.join(p.get_text(strip=True) for p in paragraphs)
            comment_text = re.sub(r'\s+', ' ', comment_text).strip()

            if not comment_text:
                continue

            # Добавляем результат
            results.append({
                "код": full_code,
                "номер ошибочной строки": line_number,
                "комментарий": comment_text
            })

    return results


if __name__ == "__main__":
    file_path = 'Ревью кода ученика.html' # название .html страницы передаем сюда

    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()

    items = extract_full_code_and_comments(html)

    with open('artifacts.json', 'w', encoding='utf-8') as f:
        import json
        json.dump(items, f, ensure_ascii=False, indent=2)
