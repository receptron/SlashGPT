from typing import List

import torch
from lib.llms.engine.base import LLMEngineBase
from lib.manifest import Manifest
from transformers import AutoModelForCausalLM, AutoTokenizer

# pip install transformers, sentencepiece, torch

# https://huggingface.co/rinna/bilingual-gpt-neox-4b-instruction-sft/blob/main/README.md


def get_role_japanese(role: str):
    if role == "user":
        return "ユーザー"
    if role == "system":
        return "システム"
    if role == "assistant":
        return "システム"
    return "システム"


# role user, system, assistant
def get_prompt_data(messages: List[dict], manifest: Manifest):
    functions = manifest.functions()
    prompts = []
    for message in messages:
        role = get_role_japanese(message["role"])
        content = message["content"]
        if content:
            prompts.append(f"{role}: {content}")
    if functions:
        # insert before last
        last = prompts.pop()
        prompts.append(
            f"system: Here is the definition of functions available to you to call.\n{functions}\nYou need to generate a json file with 'name' for function name and 'arguments' for argument."
        )
        prompts.append(last)
    prompts.append("システム:")
    return "\n".join(prompts)


class LLMEngineFromPretrained2(LLMEngineBase):
    def __init__(self, llm_model):
        model_name = llm_model.name()

        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        # self.tokenizer.do_lower_case = True

        self.type = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = self.model.to(self.type)

        return

    def chat_completion(self, messages: List[dict], manifest: Manifest, verbose: bool):
        prompt = get_prompt_data(messages, manifest)

        token_ids = self.tokenizer.encode(prompt, add_special_tokens=False, return_tensors="pt")

        with torch.no_grad():
            output_ids = self.model.generate(
                token_ids.to(self.model.device),
                max_new_tokens=512,
                do_sample=True,
                temperature=1.0,
                top_p=0.85,
                pad_token_id=self.tokenizer.pad_token_id,
                bos_token_id=self.tokenizer.bos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        output = self.tokenizer.decode(output_ids.tolist()[0][token_ids.size(1) :])
        # print(output)

        res = "".join(output)
        role = "assistant"
        return (role, res, None)
