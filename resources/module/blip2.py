import requests
import torch
from PIL import Image
from transformers import AutoProcessor, Blip2ForConditionalGeneration


def generated_text_from_image_url(url: str):
    image = Image.open(requests.get(url, stream=True).raw).convert("RGB")

    processor = AutoProcessor.from_pretrained("Salesforce/blip2-opt-2.7b")
    model = Blip2ForConditionalGeneration.from_pretrained("Salesforce/blip2-opt-2.7b")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    inputs = processor(image, return_tensors="pt").to(device)

    generated_ids = model.generate(**inputs, max_new_tokens=20)
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()

    return ({"result": "success", "text": generated_text}, None)
