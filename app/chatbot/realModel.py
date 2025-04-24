import torch
from transformers import AutoTokenizer, pipeline

class TinyLlamaChatModel:
    def __init__(self, model_name: str, use_local: bool = True):
        self.use_local = use_local
        if use_local:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.pipe = pipeline(
                "text-generation",
                model=model_name,
                torch_dtype=torch.bfloat16,
                device_map="auto"
            )

    def generate_response(self, user_message: str, context: str = "", max_new_tokens: int = 256) -> str:
        if not self.use_local:
            return "API mode not implemented yet."

        messages = []
        if context:
            messages.append({"role": "system", "content": f"Context:\n\n{context}"})
        messages.append({"role": "user", "content": user_message})

        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        outputs = self.pipe(prompt, max_new_tokens=max_new_tokens, do_sample=True, temperature=0.7)

        full_response = outputs[0]["generated_text"]
        return full_response.split("<|assistant|>")[-1].strip()
