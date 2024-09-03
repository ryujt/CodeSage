import logging

def translate_to_english(text):
    from SageLibs.web_requests import get_chat_response_ollama 

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
    lines = lines.splitlines() if isinstance(lines, str) else lines
    translated_content = []
    lines_to_translate = []
    leading_spaces = []

    for line_number, line in enumerate(lines, 1):
        stripped_line = line.strip()
        if stripped_line:  # Process only non-empty lines
            if is_english_or_code(stripped_line):
                # If English or code, translate previously collected non-English lines
                if lines_to_translate:
                    try:
                        translated_text = translate_to_english('\n'.join(lines_to_translate))
                        translated_lines = translated_text.split('\n')
                        for i, translated_line in enumerate(translated_lines):
                            if i < len(leading_spaces):
                                translated_content.append(leading_spaces[i] + translated_line)
                            else:
                                translated_content.append(translated_line)
                        logging.debug(f"Lines {line_number-len(lines_to_translate)}-{line_number-1} (Translated):\n{translated_text}")
                    except Exception as e:
                        logging.error(f"Translation error: {str(e)}")
                        # If an error occurs, add the original text
                        for i, original_line in enumerate(lines_to_translate):
                            translated_content.append(leading_spaces[i] + original_line)
                        logging.debug(f"Lines {line_number-len(lines_to_translate)}-{line_number-1} (Original kept due to error)")
                    logging.debug(f"Original:\n{chr(10).join(lines_to_translate)}")
                    lines_to_translate = []
                    leading_spaces = []
                
                translated_content.append(line)
                logging.debug(f"Line {line_number} (Original): {line}")
            else:
                leading_space = line[:len(line) - len(line.lstrip())]
                lines_to_translate.append(stripped_line)
                leading_spaces.append(leading_space)
        else:
            # Translate collected non-English lines when encountering an empty line
            if lines_to_translate:
                try:
                    translated_text = translate_to_english('\n'.join(lines_to_translate))
                    translated_lines = translated_text.split('\n')
                    for i, translated_line in enumerate(translated_lines):
                        if i < len(leading_spaces):
                            translated_content.append(leading_spaces[i] + translated_line)
                        else:
                            translated_content.append(translated_line)
                    logging.debug(f"Lines {line_number-len(lines_to_translate)}-{line_number-1} (Translated):\n{translated_text}")
                except Exception as e:
                    logging.error(f"Translation error: {str(e)}")
                    # If an error occurs, add the original text
                    for i, original_line in enumerate(lines_to_translate):
                        translated_content.append(leading_spaces[i] + original_line)
                    logging.debug(f"Lines {line_number-len(lines_to_translate)}-{line_number-1} (Original kept due to error)")
                logging.debug(f"Original:\n{chr(10).join(lines_to_translate)}")
                lines_to_translate = []
                leading_spaces = []
            
            translated_content.append(line)
            logging.debug(f"Line {line_number} (Empty)")

    # Handle any remaining non-English lines at the end
    if lines_to_translate:
        try:
            translated_text = translate_to_english('\n'.join(lines_to_translate))
            translated_lines = translated_text.split('\n')
            for i, translated_line in enumerate(translated_lines):
                if i < len(leading_spaces):
                    translated_content.append(leading_spaces[i] + translated_line)
                else:
                    translated_content.append(translated_line)
            logging.debug(f"Lines {line_number-len(lines_to_translate)+1}-{line_number} (Translated):\n{translated_text}")
        except Exception as e:
            logging.error(f"Translation error: {str(e)}")
            # If an error occurs, add the original text
            for i, original_line in enumerate(lines_to_translate):
                translated_content.append(leading_spaces[i] + original_line)
            logging.debug(f"Lines {line_number-len(lines_to_translate)+1}-{line_number} (Original kept due to error)")
        logging.debug(f"Original:\n{chr(10).join(lines_to_translate)}")

    return '\n'.join(translated_content)

def translate_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return translate_lines(content)
    except IOError as e:
        logging.error(f"File reading error: {str(e)}")
        return f"Error: Failed to read file - {str(e)}"