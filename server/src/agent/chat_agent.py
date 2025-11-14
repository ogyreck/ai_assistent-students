from typing import Dict
from langchain_core.messages import trim_messages, BaseMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

from config.Config import CONFIG
from utils.logger import get_logger
from utils.prompt_loader import render_prompt

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

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}"),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ])

        chain = self.prompt | self.llm

        self.chain_with_history = RunnableWithMessageHistory(
            chain,
            get_session_history,
            input_messages_key="question",
            history_messages_key="history",
            history_factory_config=[],
        )

        logger.info("ChatAgent initialized successfully")

    def chat(self, session_id: str, message: str) -> str:
        logger.info(f"Processing chat message for session {session_id}")

        try:
            system_prompt = render_prompt("general_system_prompt")
            message = render_prompt("sample_dialog", question=message)

            history = get_session_history(session_id)
            trimmed_history = trim_history(history.messages)
            history.clear()
            for msg in trimmed_history:
                history.add_message(msg)

            logger.info(f"system_prompt - {system_prompt}")
            logger.info(f"message - {message}")

            response = self.chain_with_history.invoke(
                {
                    "system_prompt": system_prompt,
                    "question": message,
                },
                config={"configurable": {"session_id": session_id}}
            )

            if isinstance(response, AIMessage):
                result = response.content
            else:
                result = str(response)

            logger.info(f"Chat response generated for session {session_id}")
            return result

        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")
            raise