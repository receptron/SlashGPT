from typing import List

import torch
from lib.llms.engine.base import LLMEngineBase
from lib.manifest import Manifest
from transformers import AutoModelForCausalLM, AutoTokenizer

# pip install transformers, sentencepiece, torch


def get_prompt_data(messages: List[dict], manifest: Manifest):
    functions = manifest.functions()
    prompts = []
    for message in messages:
        role = message["role"]
        content = message["content"]
        if content:
            prompts.append(f"{role}:{content}")
    if functions:
        # insert before last
        last = prompts.pop()
        prompts.append(
            f"system: Here is the definition of functions available to you to call.\n{functions}\nYou need to generate a json file with 'name' for function name and 'arguments' for argument."
        )
        prompts.append(last)
    prompts.append("assistant:")
    return "\n".join(prompts)


class LLMEngineFromPretrained(LLMEngineBase):
    def __init__(self, llm_model):
        model_name = llm_model.name()

        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
        self.tokenizer.do_lower_case = True

        self.type = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.model = self.model.to(self.type)

        return

    def chat_completion(self, messages: List[dict], manifest: Manifest, verbose: bool):
        prompt = get_prompt_data(messages, manifest)
        return_num = 1

        input_ids = self.tokenizer.encode(prompt, return_tensors="pt", add_special_tokens=False).to(self.type)
        with torch.no_grad():
            output = self.model.generate(
                input_ids,
                max_length=800,
                min_length=100,
                do_sample=True,
                top_k=500,
                top_p=0.95,
                pad_token_id=self.tokenizer.pad_token_id,
                bos_token_id=self.tokenizer.bos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                num_return_sequences=return_num,
            )
        decoded = self.tokenizer.batch_decode(output, skip_special_tokens=True)

        res = "\n".join(decoded)
        role = "assistant"
        return (role, res, None)
