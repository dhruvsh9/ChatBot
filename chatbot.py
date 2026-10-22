import os
from dotenv import load_dotenv
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL_ID = os.getenv("HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.3")

if not HF_TOKEN or HF_TOKEN == "your_huggingface_token_here":
    raise ValueError(
        "Please set your HF_TOKEN in .env file. "
        "Get a token from https://huggingface.co/settings/tokens"
    )

llm_endpoint = HuggingFaceEndpoint(
    repo_id=HF_MODEL_ID,
    huggingfacehub_api_token=HF_TOKEN,
    task="text-generation",
    max_new_tokens=512,
    temperature=0.7,
    top_p=0.95,
    repetition_penalty=1.1,
)

llm = ChatHuggingFace(llm=llm_endpoint)

SYSTEM_PROMPT = """You are a helpful, harmless, and honest AI assistant. 
Answer questions directly and concisely. If you don't know something, say so."""

prompt = PromptTemplate(
    input_variables=["history", "input"],
    template=SYSTEM_PROMPT + "\n\nCurrent conversation:\n{history}\nHuman: {input}\nAI:"
)

memory = ConversationBufferMemory(
    memory_key="history",
    return_messages=False,
    ai_prefix="AI",
    human_prefix="Human"
)

chain = ConversationChain(
    llm=llm,
    memory=memory,
    prompt=prompt,
    verbose=False
)

def main():
    print(f"🤖 Chatbot ready! Using model: {HF_MODEL_ID}")
    print("Type 'exit', 'quit', or 'bye' to end the conversation.\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ("exit", "quit", "bye"):
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            response = chain.invoke({"input": user_input})
            print(f"AI: {response['response']}\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    main()