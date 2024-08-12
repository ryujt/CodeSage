import logging
from SageLibs.web_requests import get_chat_response_ollama

class Translator:
    def __init__(self, ollama_url="http://localhost:11434/api/generate"):
        self.ollama_url = ollama_url

    def translate_to_english(self, text):
        message = f"Translate all non-English text into English in the article below. Maintain the original text structure, including spaces and line breaks. Output as plain text, not markdown.\n___\n{text}"
        result = get_chat_response_ollama(message)
        result = '\n'.join(line for line in result.splitlines() if line.strip())
        return result

    def is_english_or_code(self, text):
        for i, char in enumerate(text):
            if char.isspace() or char in '.,;:!?-_()[]{}\'"`+*&^%$#@~<>|/\\=':
                continue
            if not (char.isascii() and char.isalnum()):
                logging.info(f"Non-English character detected: '{char}' (Unicode: U+{ord(char):04X}) at position {i} in text: '{text}'")
                return False
        return True

    def translate_file(self, file_path):
        translated_content = []
        lines_to_translate = []
        leading_spaces = []

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_number, line in enumerate(file, 1):
                    stripped_line = line.strip()
                    if stripped_line:  # Process only non-empty lines
                        if self.is_english_or_code(stripped_line):
                            # If English or code, translate previously collected Korean lines
                            if lines_to_translate:
                                self._translate_and_append(lines_to_translate, leading_spaces, translated_content, line_number)
                                lines_to_translate = []
                                leading_spaces = []
                            
                            translated_content.append(line.rstrip('\n'))
                            print(f"Line {line_number} (Original): {line.rstrip()}")
                        else:
                            leading_space = line[:len(line) - len(line.lstrip())]
                            lines_to_translate.append(stripped_line)
                            leading_spaces.append(leading_space)
                    else:
                        # Translate collected Korean lines when encountering an empty line
                        if lines_to_translate:
                            self._translate_and_append(lines_to_translate, leading_spaces, translated_content, line_number)
                            lines_to_translate = []
                            leading_spaces = []
                        
                        translated_content.append(line.rstrip('\n'))
                        print(f"Line {line_number} (Empty)")

            # Handle any remaining Korean lines at the end of the file
            if lines_to_translate:
                self._translate_and_append(lines_to_translate, leading_spaces, translated_content, line_number)

        except IOError as e:
            logging.error(f"File reading error: {str(e)}")
            return f"Error: Failed to read file - {str(e)}"

        return '\n'.join(translated_content)

    def _translate_and_append(self, lines_to_translate, leading_spaces, translated_content, line_number):
        try:
            translated_text = self.translate_to_english('\n'.join(lines_to_translate))
            translated_lines = translated_text.split('\n')
            for i, translated_line in enumerate(translated_lines):
                if i < len(leading_spaces):
                    translated_content.append(leading_spaces[i] + translated_line)
                else:
                    translated_content.append(translated_line)
            print(f"Lines {line_number-len(lines_to_translate)}-{line_number-1} (Translated):\n{translated_text}")
        except Exception as e:
            logging.error(f"Translation error: {str(e)}")
            # If an error occurs, add the original text
            for i, original_line in enumerate(lines_to_translate):
                translated_content.append(leading_spaces[i] + original_line)
            print(f"Lines {line_number-len(lines_to_translate)}-{line_number-1} (Original kept due to error)")
        print(f"Original:\n{chr(10).join(lines_to_translate)}")
