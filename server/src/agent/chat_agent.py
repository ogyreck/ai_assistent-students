from typing import Dict
from langchain_core.messages import trim_messages, BaseMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.agents import create_tool_calling_agent, AgentExecutor

from config.Config import CONFIG
from utils.logger import get_logger
from utils.prompt_loader import render_prompt
from agent.tools.rag_search import search_in_documents

logger = get_logger(__name__)

store: Dict[str, ChatMessageHistory] = {}


def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


def trim_history(messages: list[BaseMessage]) -> list[BaseMessage]:
    return trim_messages(
        messages,
        max_tokens=7,
        strategy="last",
        token_counter=len,
        include_system=True,
    )


class ChatAgent:
    def __init__(self):
        logger.info("Initializing ChatAgent")

        self.llm = ChatOpenAI(
            base_url=CONFIG.llm.url,
            api_key=CONFIG.llm.token,
            model=CONFIG.llm.model,
            temperature=0.7,
        )

        self.tools = [search_in_documents]

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)

        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
        )

        logger.info("ChatAgent with RAG tool initialized successfully")

    def chat(self, session_id: str, message: str) -> str:
        logger.info(f"Processing chat message for session {session_id}")

        try:
            system_prompt = render_prompt("sample_dialog", question=message)

            history = get_session_history(session_id)
            trimmed_history = trim_history(history.messages)

            response = self.agent_executor.invoke(
                {
                    "system_prompt": system_prompt,
                    "question": message,
                    "history": trimmed_history,
                }
            )

            result = response.get("output", str(response))

            history.add_user_message(message)
            history.add_ai_message(result)

            logger.info(f"Chat response generated for session {session_id}")
            return result

        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")
            raise