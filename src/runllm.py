

import asyncio
from langchain_core.tools import tool
from model_providers import LLMFactory

factory = LLMFactory()

# ─── Math Tool ────────────────────────────────────────────────────────────────

@tool
def math_tool(operation: str, a: float, b: float) -> float:
    """
    Perform basic math operations.

    Args:
        operation: The operation to perform — 'add', 'subtract', 'multiply', 'divide'
        a: First number
        b: Second number
    """
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    else:
        raise ValueError(f"Unknown operation '{operation}'. Use: add, subtract, multiply, divide")


# ─── 1. Normal invoke ─────────────────────────────────────────────────────────

def test_invoke():
    print("\n" + "─" * 50)
    print("1. Normal invoke")
    print("─" * 50)
    llm = factory.get_llm("nebius", model_name="MiniMaxAI/MiniMax-M2.5", temperature=0.5)
    response = llm.invoke("What is Python?")
    print(response.content)


# ─── 2. Streaming ─────────────────────────────────────────────────────────────

def test_stream():
    print("\n" + "─" * 50)
    print("2. Streaming")
    print("─" * 50)
    llm = factory.get_llm("nebius", model_name="MiniMaxAI/MiniMax-M2.5", temperature=0.5)
    for chunk in llm.stream("Tell me a short story of a rabbit"):
        print(chunk.content, end="", flush=True)
    print()


# ─── 3. Async invoke ──────────────────────────────────────────────────────────

async def test_ainvoke():
    print("\n" + "─" * 50)
    print("3. Async invoke")
    print("─" * 50)
    llm = factory.get_llm("nebius", model_name="MiniMaxAI/MiniMax-M2.5", temperature=0.5)
    response = await llm.ainvoke("What is Python?")
    print(response.content)


# ─── 4. Async streaming ───────────────────────────────────────────────────────

async def test_astream():
    print("\n" + "─" * 50)
    print("4. Async streaming")
    print("─" * 50)
    llm = factory.get_llm("nebius", model_name="MiniMaxAI/MiniMax-M2.5", temperature=0.5)
    async for chunk in llm.astream("Tell me a short story of a rabbit"):
        print(chunk.content, end="", flush=True)
    print()


# ─── 5. Tool calling ──────────────────────────────────────────────────────────

def test_tool_calling():
    print("\n" + "─" * 50)
    print("5. Tool calling")
    print("─" * 50)
    llm = factory.get_llm("openai", model_name="gpt-4o", temperature=0)
    llm_with_tools = llm.bind_tools([math_tool])

    response = llm_with_tools.invoke("What is 25 multiplied by 4?")

    if response.tool_calls:
        for call in response.tool_calls:
            print(f"Tool  : {call['name']}")
            print(f"Args  : {call['args']}")
            result = math_tool.invoke(call["args"])
            print(f"Result: {result}")
    else:
        print("No tool calls made.")


# ─── Run all ──────────────────────────────────────────────────────────────────

async def main():
    # test_invoke()
    # test_stream()
    await test_ainvoke()
    # await test_astream()
    # test_tool_calling()


if __name__ == "__main__":
    print(f"Available providers: {factory.available_providers}")
    asyncio.run(main())