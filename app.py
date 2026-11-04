import json
import requests
import streamlit as st

st.set_page_config(
  page_title="Jst Ask",
  page_icon="💬",
  layout="centered",
)

OLLAMA_URL = "http://localhost:11434"

if "messages" not in st.session_state:
  st.session_state.messages = []

if "model" not in st.session_state:
  st.session_state.model = "llama3.2:3b"

@st.cache_data(ttl=10)
def get_models():
    response = requests.get(
        f"{OLLAMA_URL}/api/tags",
        timeout=5,
    )
    response.raise_for_status()

    return [
        model["name"]
        for model in response.json().get("models", [])
    ]

def ask_ollama(model, messages):
    with requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": True,
        },
        stream=True,
        timeout=(10, 600),
    ) as response:

        response.raise_for_status()

        for line in response.iter_lines():
            if not line:
                continue

            data = json.loads(line)

            content = data.get("message", {}).get(
                "content", ""
            )

            if content:
                yield content

st.title("💬 Your Friendly Neighbourhood")
st.caption("Your local AI assistant")

with st.sidebar:
    st.header("Settings")

    try:
        models = get_models()

        if not models:
            st.warning("No Ollama models found.")
        else:
            if st.session_state.model not in models:
                st.session_state.model = models[0]

            selected_model = st.selectbox(
                "Choose a model",
                models,
                index=models.index(st.session_state.model),
            )

            if selected_model != st.session_state.model:
                st.session_state.model = selected_model
                st.session_state.messages = []
                st.rerun()

            if st.button(
                "Clear conversation",
                use_container_width=True,
            ):
                st.session_state.messages = []
                st.rerun()

    except requests.RequestException:
        models = []
        st.error(
            "Cannot connect to Ollama. "
            "Check whether Ollama is running."
        )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input(
    "Ask something...",
    disabled=not models,
)

if prompt:
    # Save the user's message.
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
    })

    # Display it immediately.
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate and display the AI response.
    with st.chat_message("assistant"):
        try:
            answer = st.write_stream(
                ask_ollama(
                    st.session_state.model,
                    st.session_state.messages,
                )
            )

            if answer:
                # Save the answer for future questions.
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                })
            else:
                st.warning("The model returned no text.")

        except (
            requests.RequestException,
            ValueError,
        ) as error:
            st.error(f"Could not get a response: {error}")