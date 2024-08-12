import logging
from SageLibs.web_requests import get_chat_response_ollama

def translate_to_english(text):
    message = f"""Translate all non-English text into English in the article below.
Follow these rules strictly:
1. Maintain the original text structure, including spaces and line breaks.
2. If you cannot translate any part, return that part unchanged.
3. Do not add any explanations, comments, or notes about the translation.
4. Do not describe the content or structure of the text.
5. Only return the translated text, nothing else.
---
{text}
"""
    
    result = get_chat_response_ollama(message)
    result = '\n'.join(line for line in result.splitlines() if line.strip())
    return result

def is_english_or_code(text):
    for i, char in enumerate(text):
        if char.isspace() or char in '.,;:!?-_()[]{}\'"`+*&^%$#@~<>|/\\=':
            continue
        if not (char.isascii() and char.isalnum()):
            logging.info(f"Non-English character detected: '{char}' (Unicode: U+{ord(char):04X}) at position {i} in text: '{text}'")
            return False
    return True

def translate_lines(lines):
    pass

def translate_file(file_path):
    translated_content = []
    lines_to_translate = []
    leading_spaces = []

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, 1):
                stripped_line = line.strip()
                if stripped_line:  # 빈 줄이 아닌 경우에만 처리
                    if is_english_or_code(stripped_line):
                        # 영어나 코드인 경우, 이전에 모아둔 한글 라인들을 번역
                        if lines_to_translate:
                            try:
                                translated_text = translate_to_english('\n'.join(lines_to_translate))
                                translated_lines = translated_text.split('\n')
                                for i, translated_line in enumerate(translated_lines):
                                    if i < len(leading_spaces):
                                        translated_content.append(leading_spaces[i] + translated_line)
                                    else:
                                        translated_content.append(translated_line)
                                print(f"Lines {line_number-len(lines_to_translate)}-{line_number-1} (Translated):\n{translated_text}")
                            except Exception as e:
                                logging.error(f"Translation error: {str(e)}")
                                # 오류 발생 시 원문 그대로 추가
                                for i, original_line in enumerate(lines_to_translate):
                                    translated_content.append(leading_spaces[i] + original_line)
                                print(f"Lines {line_number-len(lines_to_translate)}-{line_number-1} (Original kept due to error)")
                            print(f"Original:\n{chr(10).join(lines_to_translate)}")
                            lines_to_translate = []
                            leading_spaces = []
                        
                        translated_content.append(line.rstrip('\n'))
                        print(f"Line {line_number} (Original): {line.rstrip()}")
                    else:
                        leading_space = line[:len(line) - len(line.lstrip())]
                        lines_to_translate.append(stripped_line)
                        leading_spaces.append(leading_space)
                else:
                    # 빈 줄을 만났을 때도 이전에 모아둔 한글 라인들을 번역
                    if lines_to_translate:
                        try:
                            translated_text = translate_to_english('\n'.join(lines_to_translate))
                            translated_lines = translated_text.split('\n')
                            for i, translated_line in enumerate(translated_lines):
                                if i < len(leading_spaces):
                                    translated_content.append(leading_spaces[i] + translated_line)
                                else:
                                    translated_content.append(translated_line)
                            print(f"Lines {line_number-len(lines_to_translate)}-{line_number-1} (Translated):\n{translated_text}")
                        except Exception as e:
                            logging.error(f"Translation error: {str(e)}")
                            # 오류 발생 시 원문 그대로 추가
                            for i, original_line in enumerate(lines_to_translate):
                                translated_content.append(leading_spaces[i] + original_line)
                            print(f"Lines {line_number-len(lines_to_translate)}-{line_number-1} (Original kept due to error)")
                        print(f"Original:\n{chr(10).join(lines_to_translate)}")
                        lines_to_translate = []
                        leading_spaces = []
                    
                    translated_content.append(line.rstrip('\n'))
                    print(f"Line {line_number} (Empty)")

        # 파일의 끝에 도달했을 때 남아있는 한글 라인들 처리
        if lines_to_translate:
            try:
                translated_text = translate_to_english('\n'.join(lines_to_translate))
                translated_lines = translated_text.split('\n')
                for i, translated_line in enumerate(translated_lines):
                    if i < len(leading_spaces):
                        translated_content.append(leading_spaces[i] + translated_line)
                    else:
                        translated_content.append(translated_line)
                print(f"Lines {line_number-len(lines_to_translate)+1}-{line_number} (Translated):\n{translated_text}")
            except Exception as e:
                logging.error(f"Translation error: {str(e)}")
                # 오류 발생 시 원문 그대로 추가
                for i, original_line in enumerate(lines_to_translate):
                    translated_content.append(leading_spaces[i] + original_line)
                print(f"Lines {line_number-len(lines_to_translate)+1}-{line_number} (Original kept due to error)")
            print(f"Original:\n{chr(10).join(lines_to_translate)}")

    except IOError as e:
        logging.error(f"파일 읽기 오류: {str(e)}")
        return f"Error: Failed to read file - {str(e)}"

    return '\n'.join(translated_content)