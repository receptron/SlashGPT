from __future__ import annotations

from typing import TYPE_CHECKING, List

import replicate

from slashgpt.llms.engine.base import LLMEngineBase
from slashgpt.utils.print import print_debug

if TYPE_CHECKING:
    from slashgpt.manifest import Manifest


default_model = "a16z-infra/llama7b-v2-chat:a845a72bb3fa3ae298143d13efa8873a2987dbf3d49c293513cd8abf4b845a83"


class LLMEngineReplicate(LLMEngineBase):
    def chat_completion(self, messages: List[dict], manifest: Manifest, verbose: bool):
        temperature = manifest.temperature()

        replicate_model = self.llm_model.get("replicate_model") or default_model
        prompt = self.prompt_from_messages(messages, manifest)

        if verbose:
            print_debug("calling replicate.run")

        output = replicate.run(
            replicate_model,
            input={"prompt": prompt},
            temperature=temperature,
        )
        res = "".join(output)
        function_call = self._extract_function_call(messages[-1], manifest, res) if manifest.functions() is not None else None

        role = "assistant"
        if function_call:
            return (role, None, function_call, None)
        else:
            return (role, res, None, None)
