def escape_markdown(text: object) -> str:
    value = "" if text is None else str(text)
    for char in ("\\", "_", "*", "`", "[", "]"):
        value = value.replace(char, f"\\{char}")
    return value

def normalize_text_key(text: object) -> str:
    value = "" if text is None else str(text).lower()
    cleaned = []
    previous_space = False
    for char in value:
        if char.isalnum():
            cleaned.append(char)
            previous_space = False
        elif not previous_space:
            cleaned.append(" ")
            previous_space = True
    return " ".join("".join(cleaned).split())
