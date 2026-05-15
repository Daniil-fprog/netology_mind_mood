import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_NAME = "Helsinki-NLP/opus-mt-ru-en"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

# Для MVP лучше CPU. На M2 8GB так стабильнее.
device = torch.device("cpu")
model.to(device)
model.eval()

def translate_to_english(text: str) -> str:
    """
    Функция для перевода текста. 
    Использует 'Helsinki-NLP/opus-mt-ru-en'
    """

    if not text or not text.strip():
        return ""
    
    inputs = tokenizer(
        text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512,
    )

    inputs = {
        key: value.to(device)
        for key, value in inputs.items()
    }

    with torch.no_grad():
        output_tokens = model.generate(
            **inputs,
            max_length=512,
            num_beams=4,
            early_stopping=True,
        )

    translated_text = tokenizer.decode(
        output_tokens[0],
        skip_special_tokens=True,
    )

    return translated_text


