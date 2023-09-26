from typing import List

from transformers import CodeLlamaTokenizer, LlamaForCausalLM

from slashgpt.llms.engine.base import LLMEngineBase
from slashgpt.llms.engine.replicate import message_to_prompt
from slashgpt.manifest import Manifest


class LLMEngineCodeLlama(LLMEngineBase):
    def __init__(self, llm_model):
        model_name = llm_model.name()
        self.tokenizer = CodeLlamaTokenizer.from_pretrained(model_name)
        self.model = LlamaForCausalLM.from_pretrained(model_name)

    def chat_completion(self, messages: List[dict], manifest: Manifest, verbose: bool):
        prompt = message_to_prompt(messages, manifest)

        input_ids = self.tokenizer(prompt, return_tensors="pt")["input_ids"]
        generated_ids = self.model.generate(input_ids, max_new_tokens=128, pad_token_id=100)

        filling = self.tokenizer.batch_decode(generated_ids[:, input_ids.shape[1] :], skip_special_tokens=True)[0]
        res = filling.replace("\\begin{code}", "```").replace("\\end{code}", "```")

        function_call = self._extract_function_call(messages[-1], manifest, res)

        role = "assistant"
        if function_call:
            return (role, None, function_call)
        else:
            return (role, filling, None)
