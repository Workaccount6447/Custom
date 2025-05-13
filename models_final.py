class Model:
    def __init__(self, model_id, name, description, command=None):
        self.model_id = model_id
        self.name = name
        self.description = description
        self.command = command or model_id.split('/')[1].split(':')[0].replace('-', '').replace('.', '').lower()

models = [
    Model("google/gemma-3-4b-it:free", "Google: Gemma 3 4B (free)", "Gemma 3 introduces multimodality, supporting vision-language input and text outputs."),
    Model("qwen/qwq-32b:free", "Qwen: QWQ 32B (free)", "A distilled version of the DeepSeek-R1 model, optimized for reasoning domains like mathematics, coding, and logic."),
    Model("rekaai/reka-flash-3:free", "RekaAI: Reka Flash 3 (free)", "Experimental release with limited multilingual understanding capabilities."),
    Model("google/gemma-3-12b-it:free", "Google: Gemma 3 12B (free)", "Part of the Gemma 3 family, offering improved math, reasoning, and chat capabilities."),
    Model("moonshotai/moonlight-16b-a3b-instruct:free", "MoonShotAI: MoonLight 16B A3B Instruct (free)", "Optimized for low-latency performance across common AI tasks."),
    Model("google/gemma-2-9b-it:free", "Google: Gemma 2 9B (free)", "Open-source language model suitable for text generation tasks.", command="chatgpt"),
]
