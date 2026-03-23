## LangChain Streaming

### 1. What Streaming Means in LangChain

Streaming allows an LLM to **send tokens incrementally while generating the response**, instead of waiting for the entire output.

Normal flow:

```
User → LLM → Full response returned
```

Streaming flow:

```
User → LLM → token1 → token2 → token3 → ... → final response
```

Benefits:

* Lower perceived latency
* Better UX for chat applications
* Enables real-time UI updates
* Useful for agents and tool execution monitoring

---

# 2. Types of Streaming in LangChain

LangChain provides **three main streaming patterns**.

| Type               | Purpose                       |
| ------------------ | ----------------------------- |
| Token streaming    | Stream generated tokens       |
| Event streaming    | Stream agent events           |
| Callback streaming | Handle tokens using callbacks |

---

# 3. Token Streaming

Token streaming is the **most common method**.
The model sends tokens as they are generated.

Example using a chat model.

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o",
    streaming=True
)

for chunk in llm.stream("Explain RAG in simple terms"):
    print(chunk.content, end="", flush=True)
```

What happens internally:

```
LLM generates token
↓
LangChain receives token
↓
Token returned in chunk
↓
Printed immediately
```

Typical output:

```
Retrieval Augmented Generation is a method...
```

Tokens appear gradually.

---

# 4. Streaming with Runnable Interface (LangChain v1)

LangChain uses the **Runnable interface** for pipelines.

Streaming works directly with `.stream()`.

Example:

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

prompt = ChatPromptTemplate.from_template("Explain {topic}")

model = ChatOpenAI(streaming=True)

chain = prompt | model

for chunk in chain.stream({"topic": "vector databases"}):
    print(chunk.content, end="")
```

Pipeline:

```
Input
 ↓
Prompt Template
 ↓
LLM
 ↓
Stream tokens
```

---

# 5. Async Streaming

For async applications (FastAPI, websockets).

Use `.astream()`.

```python
async for chunk in chain.astream({"topic": "RAG"}):
    print(chunk.content, end="")
```

Useful for:

* APIs
* real-time web apps
* chat interfaces

---

# 6. Callback Streaming

Callbacks allow capturing tokens as they arrive.

Typical use cases:

* logging
* streaming to UI
* storing tokens

Example:

```python
from langchain.callbacks.base import BaseCallbackHandler

class MyHandler(BaseCallbackHandler):

    def on_llm_new_token(self, token, **kwargs):
        print(token, end="")

llm = ChatOpenAI(
    streaming=True,
    callbacks=[MyHandler()]
)

llm.invoke("Explain embeddings")
```

Callback triggers every time a new token arrives.

---

# 7. Streaming with Agents

Streaming can also show **agent reasoning steps**.

Example:

```python
agent_executor.stream(
    {"messages": [("user", "Find population of Japan")]},
    stream_mode="values"
)
```

Stream modes:

| Mode     | Output               |
| -------- | -------------------- |
| values   | final messages       |
| updates  | tool execution steps |
| messages | token stream         |

---

# 8. Streaming Events

LangChain supports **event streaming** using `.astream_events()`.

Example:

```python
async for event in chain.astream_events(
    {"topic": "RAG"},
    version="v1"
):
    print(event)
```

Events include:

```
on_chain_start
on_llm_start
on_llm_new_token
on_llm_end
on_chain_end
```

Useful for:

* debugging pipelines
* observability
* agent monitoring

---

# 9. Streaming with RAG

Streaming works the same in a RAG pipeline.

Example architecture:

```
User Query
     ↓
Retriever
     ↓
Documents
     ↓
Prompt Template
     ↓
LLM
     ↓
Stream tokens to user
```

Example code:

```python
chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | model
)

for chunk in chain.stream("What is vector search"):
    print(chunk.content, end="")
```

---

# 10. Streaming in Chat Applications

Typical chat UI architecture:

```
User Message
     ↓
Backend API
     ↓
LangChain streaming
     ↓
Send tokens via WebSocket / SSE
     ↓
Frontend displays tokens
```

Technologies used:

* FastAPI
* Server Sent Events (SSE)
* WebSockets
* React streaming UI

---

# 11. Streaming with FastAPI (Example)

Example server streaming response.

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

def generate():
    for chunk in chain.stream({"topic": "RAG"}):
        yield chunk.content

@app.get("/stream")
def stream():
    return StreamingResponse(generate(), media_type="text/plain")
```

Client receives tokens continuously.

---

# 12. Streaming with Different Providers

Streaming support depends on the model provider.

Common providers supporting streaming:

* OpenAI
* Anthropic
* Groq
* Google Gemini

Most require:

```
stream=True
```

---

# 13. Streaming vs Non-Streaming

| Feature       | Streaming       | Non-Streaming |
| ------------- | --------------- | ------------- |
| Latency       | Low perceived   | Higher        |
| Output        | token by token  | full response |
| UI experience | better          | basic         |
| Complexity    | slightly higher | simple        |

---

# 14. Best Practices

### Enable streaming only when needed

Streaming adds overhead.

Good for:

* chat
* assistants
* real-time apps

---

### Buffer tokens if needed

Sometimes tokens must be combined before sending to UI.

---

### Handle partial responses

Streaming may stop if:

* network breaks
* model stops early

---

### Monitor with observability

Streaming pipelines are harder to debug.

Common tools:

* LangSmith
* logging callbacks

---

# 15. Common Problems

### Tokens arrive without spaces

Some tokenizers split words.

Example:

```
Retrieval
Augmented
Generation
```

Solution: accumulate tokens before displaying.

---

### Tool outputs interrupt stream

Agents may pause streaming while executing tools.

---

### Rate limits

Streaming requests still count toward rate limits.

---

# 16. When to Use Streaming

Use streaming for:

* chatbots
* AI assistants
* coding copilots
* long answers
* research assistants

Not necessary for:

* classification
* embeddings
* short responses

---

## Quick Mental Model

```
LLM generates token
        ↓
LangChain receives token
        ↓
stream() yields token
        ↓
UI prints token
```

---

If useful, the next advanced topics are:

* **LangChain streaming with WebSockets**
* **Streaming RAG with LangGraph**
* **Multi-model streaming pipelines**
* **Streaming agent tool execution**
