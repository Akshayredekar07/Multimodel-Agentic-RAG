from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from config import config

# Old direct setup (kept commented as requested)
# groq_api_key = os.getenv("GROQ__API_KEY")
# if groq_api_key is None:
#     raise RuntimeError("Missing GROQ__API_KEY in environment or .env")
# os.environ["GROQ_API_KEY"] = groq_api_key
#
# model = init_chat_model(
#     "groq:moonshotai/kimi-k2-instruct-0905",
#     temperature=0.7,
#     timeout=30,
#     max_tokens=1000,
#     max_retries=6,
# )

# New setup via config.py
provider_cfg = config.get_provider(config.default_provider)
provider_cfg.apply_runtime_env()

model = init_chat_model(
    provider_cfg.qualified_model,
    temperature=config.temperature,
    timeout=config.timeout,
    max_tokens=config.max_tokens,
    max_retries=config.max_retries,
)

conversation = [
    SystemMessage("You are a helpful assistant that translates English to French."),
    HumanMessage("Translate: I love programming."),
]

response = model.invoke(conversation)
print(response.content)


for chunk in model.stream("Why do parrots have colorful feathers?"):
    print(chunk.text, end="|", flush=True)
