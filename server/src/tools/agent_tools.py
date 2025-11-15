"""
Agent tools for calendar and web search operations.
These tools are executed directly and return results back to the client.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import json
import httpx
import logging
import asyncio
import time

from config.Config import CONFIG
from service.tavily_search import TavilySearchService

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CalendarTool:
    """Calendar tool for date operations and time planning."""

    @staticmethod
    async def execute(action: str, days_offset: int = 0, task_description: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute calendar action.

        Args:
            action: 'current_date', 'add_days', or 'timeline_suggestion'
            days_offset: Number of days to add/subtract (for 'add_days' action)
            task_description: Task description (for 'timeline_suggestion' action)

        Returns:
            Dictionary with success status and result
        """
        try:
            now = datetime.now()

            if action == "current_date":
                result = f"Текущая дата и время: {now.strftime('%d.%m.%Y %H:%M:%S')}"

            elif action == "add_days":
                target = now + timedelta(days=days_offset)
                days_text = f"{abs(days_offset)} день" if abs(days_offset) == 1 else f"{abs(days_offset)} дней"
                direction = "от сегодня" if days_offset >= 0 else "до сегодня"
                result = (
                    f"{days_text} {direction} ({now.strftime('%d.%m.%Y')}) это: "
                    f"{target.strftime('%d.%m.%Y')}"
                )

            elif action == "timeline_suggestion":
                if not task_description:
                    return {"success": False, "error": "Требуется описание задачи для предложения графика"}

                start = now.strftime('%d.%m.%Y')
                mid = (now + timedelta(days=5)).strftime('%d.%m.%Y')
                end = (now + timedelta(days=12)).strftime('%d.%m.%Y')
                result = (
                    f"Рекомендуемый график для: '{task_description}'\n"
                    f"📋 Планирование и исследование: {start} – {mid}\n"
                    f"✍️ Выполнение и черновик: {mid} – {end}\n"
                    f"✓ Проверка и финализация: до {end}"
                )
            else:
                return {"success": False, "error": f"Неизвестное действие: {action}"}

            logger.info(f"✓ Calendar tool executed: {action}")
            return {"success": True, "result": result}

        except Exception as e:
            logger.error(f"Calendar tool error: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def create_task(user_id: str, title: str, date: str, time: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a task in the calendar.

        Args:
            user_id: User ID
            title: Task title
            date: Task date in YYYY-MM-DD format
            time: Task time in HH:MM format
            description: Task description (optional)

        Returns:
            Dictionary with success status and created task
        """
        try:
            import uuid

            # Parse date to get year and month
            date_parts = date.split('-')
            if len(date_parts) != 3:
                return {"success": False, "error": f"Invalid date format. Use YYYY-MM-DD"}

            year = int(date_parts[0])
            month = int(date_parts[1])

            # Create task object
            task_data = {
                "id": str(uuid.uuid4()),
                "title": title,
                "date": date,
                "time": time,
                "description": description or ""
            }

            # Make HTTP request to create task
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"http://localhost:8000/api/calendar/task/{user_id}/{year}/{month}",
                    json=task_data
                )

                if response.status_code == 200:
                    logger.info(f"✓ Task created: {title} at {date} {time}")
                    return {"success": True, "result": f"✓ Задача '{title}' создана на {date} в {time}"}
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"Failed to create task: {error_msg}")
                    return {"success": False, "error": error_msg}

        except Exception as e:
            logger.error(f"Calendar create_task error: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def get_tasks_in_range(user_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get tasks in a date range.

        Args:
            user_id: User ID
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dictionary with success status and tasks list
        """
        try:
            # Make HTTP request to get tasks in range
            async with httpx.AsyncClient(timeout=10.0) as client:
                # We need to get tasks for each month in the range
                from datetime import datetime
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")

                all_tasks = []
                current = start

                # Iterate through each month in the range
                while current <= end:
                    year = current.year
                    month = current.month

                    response = await client.get(
                        f"http://localhost:8000/api/calendar/tasks/{user_id}/{year}/{month}"
                    )

                    if response.status_code == 200:
                        tasks = response.json()
                        # Filter tasks by date range
                        for task in tasks:
                            task_date = datetime.strptime(task["date"], "%Y-%m-%d")
                            if start <= task_date <= end:
                                all_tasks.append(task)

                    # Move to next month
                    if current.month == 12:
                        current = current.replace(year=current.year + 1, month=1)
                    else:
                        current = current.replace(month=current.month + 1)

                if all_tasks:
                    # Format response
                    tasks_text = f"📋 Найдено {len(all_tasks)} задач(и) в периоде с {start_date} по {end_date}:\n\n"
                    for task in all_tasks:
                        tasks_text += f"• {task['date']} {task['time']} - {task['title']}"
                        if task.get('description'):
                            tasks_text += f" ({task['description']})"
                        tasks_text += "\n"

                    logger.info(f"✓ Retrieved {len(all_tasks)} tasks for {user_id}")
                    return {"success": True, "result": tasks_text}
                else:
                    return {"success": True, "result": f"❌ Задач не найдено в периоде с {start_date} по {end_date}"}

        except Exception as e:
            logger.error(f"Calendar get_tasks_in_range error: {e}")
            return {"success": False, "error": str(e)}


class WebSearchTool:
    """Web search tool for finding information on the internet."""

    @staticmethod
    async def execute(query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Execute web search.

        Args:
            query: Search query
            max_results: Maximum number of results (1-10)

        Returns:
            Dictionary with success status and results
        """
        try:
            if not query.strip():
                return {"success": False, "error": "Поисковый запрос не может быть пустым"}

            # Clamp max_results to valid range
            max_results = max(1, min(10, max_results))

            logger.info(f"🔍 Web search query: '{query}' (max results: {max_results})")

            # Use TavilySearchService if available
            try:
                search_service = TavilySearchService()
                sources = await search_service.search(
                    query=query,
                    max_results=max_results,
                    include_raw_content=False,
                )

                results = []
                for source in sources:
                    results.append({
                        "title": source.title,
                        "url": source.url,
                        "snippet": source.snippet[:150] + "..." if len(source.snippet) > 150 else source.snippet,
                    })

                logger.info(f"✓ Web search completed: found {len(results)} results")
                return {"success": True, "results": results}

            except Exception as e:
                logger.warning(f"TavilySearchService failed: {e}, trying fallback...")
                # Fallback: return a simple message
                return {
                    "success": True,
                    "results": [
                        {
                            "title": "Search Service Unavailable",
                            "url": "#",
                            "snippet": "Сервис поиска временно недоступен. Пожалуйста, попробуйте позже."
                        }
                    ]
                }

        except Exception as e:
            logger.error(f"Web search error: {e}")
            return {"success": False, "error": str(e)}


class ReActAgent:
    """
    ReAct (Reasoning + Acting) agent that decides when to use tools.
    The agent works autonomously and determines when it has completed the task.
    """

    def __init__(self, llm_client, rag_service=None):
        self.llm_client = llm_client
        self.rag_service = rag_service
        self.max_iterations = 10  # Prevent infinite loops
        self.current_iteration = 0
        self.tool_history = []
        self.start_time = None
        self.timeout_seconds = 40  # 40 second timeout
        self.accumulated_response = ""  # Store responses in case of timeout

    async def process_message(self, user_message: str, chat_context: list) -> tuple[str, list]:
        """
        Process user message and autonomously decide whether to use tools.
        If agent doesn't return FINAL_ANSWER within 40 seconds, returns accumulated response.

        Returns:
            (final_response, tool_calls_made)
        """
        self.current_iteration = 0
        self.tool_history = []
        self.start_time = time.time()
        self.accumulated_response = ""

        while self.current_iteration < self.max_iterations:
            self.current_iteration += 1

            # Check if timeout exceeded
            elapsed_time = time.time() - self.start_time
            if elapsed_time > self.timeout_seconds:
                logger.warning(f"⏱️ Agent timeout exceeded ({elapsed_time:.1f}s > {self.timeout_seconds}s). Returning accumulated response.")
                return self._handle_timeout_response(), self.tool_history

            # Build system prompt for agent decision-making
            system_prompt = self._build_agent_system_prompt()

            # Call LLM to decide on next action
            thought_response = await self._get_agent_decision(
                system_prompt,
                user_message,
                chat_context
            )

            # Store the response
            self.accumulated_response = thought_response

            # Parse agent response for tool calls or final answer
            action, action_input = self._parse_agent_response(thought_response)

            if action == "FINAL_ANSWER":
                # Format the final answer for human readability
                formatted_response = self._format_final_answer(action_input, self.tool_history)
                return formatted_response, self.tool_history

            elif action in ["CALENDAR", "WEBSEARCH"]:
                # Execute the tool
                result = await self._execute_tool(action, action_input)
                self.tool_history.append({
                    "tool": action,
                    "input": action_input,
                    "result": result
                })

                # Add to context for next iteration
                chat_context.append({
                    "role": "assistant",
                    "content": f"[Tool Call: {action}]\n{result}"
                })

            else:
                # Unknown action - treat as final answer
                logger.warning(f"Unknown agent action: {action}. Treating as final answer.")
                return self._handle_unknown_action(action, action_input, self.tool_history), self.tool_history

        # Fallback if max iterations reached
        logger.warning(f"Max iterations ({self.max_iterations}) reached without FINAL_ANSWER")
        return self._handle_max_iterations_response(), self.tool_history

    async def _get_agent_decision(self, system_prompt: str, user_message: str, chat_context: list) -> str:
        """Get agent decision from LLM."""
        messages = [{"role": "system", "content": system_prompt}] + chat_context

        full_response = ""
        async for chunk in self.llm_client.chat_completion_stream(
            messages=messages,
        ):
            full_response += chunk

        return full_response

    def _build_agent_system_prompt(self) -> str:
        """Build system prompt that instructs the agent to make tool decisions."""
        return f"""Ты автономный ассистент-агент, который должен решать, использовать ли инструменты для выполнения задач.

═══════════════════════════════════════════════════════════════
ДОСТУПНЫЕ ИНСТРУМЕНТЫ:
═══════════════════════════════════════════════════════════════

1. CALENDAR - для работы с датами, графиками и задачами в календаре

   ИСПОЛЬЗУЙ ЭТОТ ИНСТРУМЕНТ КОГДА:
   - Пользователь просит создать задачу в календаре
   - Пользователь просит добавить/удалить задачу из календаря
   - Пользователь просит показать задачи на определённый период
   - Пользователь просит информацию о датах и сроках

   ФОРМАТЫ КОМАНД:

   a) Создание одной задачи:
      CALENDAR[создать_задачу | название: <название> | дата: <YYYY-MM-DD> | время: <HH:MM> | описание: <опционально>]

   b) Получение задач в диапазоне дат:
      CALENDAR[получить_задачи | начало: <YYYY-MM-DD> | конец: <YYYY-MM-DD>]

   c) Получение текущей даты:
      CALENDAR[текущая_дата]

   ВАЖНЫЕ ПРАВИЛА:
   - Всегда пытайся решить задачу сам.
   - Дату ВСЕГДА указывай в формате YYYY-MM-DD (например: 2025-11-15)
   - Время в формате HH:MM (например: 10:00, 14:30)
   - Если пользователь говорит "сегодня" или "завтра" - преобразуй в конкретную дату
   - Для диапазонов: если пользователь говорит "эту неделю", "этот месяц" - конвертируй в реальные даты
   - Разделяй параметры символом "|" для ясности

2. WEBSEARCH - для поиска информации в интернете

   Формат: WEBSEARCH[запрос: <запрос>, max_results: <число>]
   Используй, когда нужна актуальная информация из интернета

═══════════════════════════════════════════════════════════════
АЛГОРИТМ ОБРАБОТКИ:
═══════════════════════════════════════════════════════════════
current_time: {datetime.now().strftime("%d,%m,%y %H:%M:%S")}

1. ПОНИМАНИЕ: Проанализируй что просит пользователь
2. ПАРСИНГ: Извлеки все необходимые параметры (дата, время, название)
3. ПРЕОБРАЗОВАНИЕ: Переведи относительные даты (сегодня, завтра, на неделю) в YYYY-MM-DD
4. ИНСТРУМЕНТ: Вызови нужный инструмент с правильно отформатированными параметрами
5. РЕЗУЛЬТАТ: Используй результат для формирования ответа пользователю

ПРИМЕРЫ:
- "Добавь задачу защиту проекта на завтра в 10 утра"
  → Преобразуй "завтра" в конкретную дату, затем используй команду:
  → CALENDAR[создать_задачу | название: защиту проекта | дата: {(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")} | время: 10:00]

- "Покажи мне задачи на эту неделю"
  → Определи начало и конец недели (сегодня: {datetime.now().strftime("%Y-%m-%d")}), затем:
  → CALENDAR[получить_задачи | начало: {(datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")} | конец: {(datetime.now() + timedelta(days=6 - datetime.now().weekday())).strftime("%Y-%m-%d")}]

- "Создай задачу 'Встреча с директором' на следующий месяц в 14:30"
  → CALENDAR[создать_задачу | название: Встреча с директором | дата: {(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")} | время: 14:30]

═══════════════════════════════════════════════════════════════
ФОРМАТ ОТВЕТА:
═══════════════════════════════════════════════════════════════

ДУМАЮ: [Логика мышления, включая преобразование дат! Обязательно в конце верни FINAL_ANSWER без него нельзя звыершить чат!!!!]
ДЕЙСТВИЕ: [CALENDAR/WEBSEARCH/FINAL_ANSWER]
[Параметры в правильном формате]

═══════════════════════════════════════════════════════════════
ТРЕБОВАНИЯ К ФИНАЛЬНОМУ ОТВЕТУ (FINAL_ANSWER):
═══════════════════════════════════════════════════════════════

Когда ты отправляешь FINAL_ANSWER, формат должен быть:

FINAL_ANSWER:
[Здесь твой понятный человеку ответ]

ВАЖНО:
- Обязательно в конце верни FINAL_ANSWER без него нельзя звыершить чат!
- Если есть ответ в доп информации сразу то не надо идти в интернет, отвечай сразу.
- Отвечай только той информацией которую ты нашёл, от себя ни чего не добавляй
- Не включай "ДУМАЮ:", "ДЕЙСТВИЕ:" в финальный ответ
- Ответ должен быть КРАТКИМ и ПОНЯТНЫМ
- Если была создана задача: "✅ Задача 'название' создана на дату в время"
- Если были найдены задачи: "📋 Найдено X задач(и) в периоде..."
- Если был поиск: "Вот что я нашел: [результаты]"
- ВСЕГДА используй эмодзи и структурирование для читаемости
"""

    def _parse_agent_response(self, response: str) -> tuple[str, str]:
        """Parse agent response to extract action and input."""
        import re
        response_lower = response.lower()

        # Check for FINAL_ANSWER
        final_answer_patterns = [
            r'final_answer:\s*\n(.*?)(?:\n(?:ДУМАЮ|ДЕЙСТВИЕ|FINAL|ОТВЕТ|$))',
            r'FINAL_ANSWER:\s*\n(.*?)(?:\n(?:ДУМАЮ|ДЕЙСТВИЕ|FINAL|ОТВЕТ|$))',
            r'ответ:\s*\n(.*?)(?:\n(?:думаю|действие|final|ответ)|$)',
            r'ОТВЕТ:\s*\n(.*?)(?:\n(?:ДУМАЮ|ДЕЙСТВИЕ|FINAL|$))',
        ]

        for pattern in final_answer_patterns:
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                answer = match.group(1).strip()
                if answer:
                    return "FINAL_ANSWER", answer

        # Check for CALENDAR
        if "calendar[" in response_lower:
            start = response_lower.find("calendar[")
            # Find the closing bracket
            bracket_count = 0
            end = start
            for i in range(start, min(start + 300, len(response))):
                if response[i] == '[':
                    bracket_count += 1
                elif response[i] == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end = i + 1
                        break
            if end > start:
                match = response[start:end]
                return "CALENDAR", match

        # Check for WEBSEARCH
        if "websearch[" in response_lower:
            start = response_lower.find("websearch[")
            # Find the closing bracket
            bracket_count = 0
            end = start
            for i in range(start, min(start + 300, len(response))):
                if response[i] == '[':
                    bracket_count += 1
                elif response[i] == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end = i + 1
                        break
            if end > start:
                match = response[start:end]
                return "WEBSEARCH", match

        # Default to final answer if no action detected
        # Clean up the response
        clean_response = response.strip()
        # Remove thinking markers if present
        for marker in ['думаю:', 'действие:', 'final_answer:', 'ответ:']:
            clean_response = re.sub(f'^.*?{marker}\\s*', '', clean_response, flags=re.IGNORECASE | re.MULTILINE)

        return "FINAL_ANSWER", clean_response if clean_response else response

    def _handle_timeout_response(self) -> str:
        """
        Handle timeout case: return formatted response based on accumulated data.
        """
        if not self.accumulated_response:
            return "⚠️ **Истёк лимит времени на обработку**\n\nИсходная обработка заняла более 40 секунд. Попробуйте переформулировать вопрос более кратко."

        # Try to extract useful information from accumulated response
        lines = self.accumulated_response.split('\n')
        useful_lines = []
        for line in lines:
            line = line.strip()
            if line and not any(marker in line.lower() for marker in ['думаю:', 'действие:', 'final_answer:', 'ответ:']):
                useful_lines.append(line)

        if useful_lines:
            response_text = '\n'.join(useful_lines[:5])  # Take first 5 useful lines
            return f"⚠️ **Ответ (из-за истечения лимита времени):**\n\n{response_text}\n\n_Обработка была прервана для обеспечения быстрого ответа._"
        else:
            return "⚠️ **Истёк лимит времени на обработку**\n\nСистема не смогла завершить обработку за отведённое время. Попробуйте переформулировать вопрос более кратко."

    def _handle_unknown_action(self, action: str, action_input: str, tool_history: list) -> str:
        """
        Handle unknown action: return what we have so far.
        """
        if action_input:
            return f"⚠️ **Неизвестное действие:** {action}\n\n{action_input}"
        else:
            return "⚠️ Не удалось определить действие для выполнения. Попробуйте переформулировать запрос."

    def _handle_max_iterations_response(self) -> str:
        """
        Handle max iterations reached: return informative error.
        """
        if self.accumulated_response:
            # Try to extract last meaningful response
            lines = self.accumulated_response.split('\n')
            useful_lines = [l.strip() for l in lines if l.strip() and not any(m in l.lower() for m in ['думаю:', 'действие:', 'final_answer:'])]
            if useful_lines:
                return f"⚠️ **Результат (достигнут лимит итераций):**\n\n{chr(10).join(useful_lines[:3])}"

        return "⚠️ **Обработка завершена с ошибкой**\n\nДостигнут максимальный лимит итераций без полного завершения. Попробуйте переформулировать запрос."

    def _format_final_answer(self, answer: str, tool_history: list) -> str:
        """
        Format the final answer for human readability.
        Extracts the answer text and adds formatting.
        """
        # Remove "ДУМАЮ:", "ДЕЙСТВИЕ:", and other markers
        lines = answer.split('\n')
        result_lines = []

        for line in lines:
            line = line.strip()
            # Skip internal markers and empty lines
            if not line:
                continue
            if line.lower() in ['думаю:', 'действие:', 'final_answer:', 'ответ:', 'final_answer', 'думаю', 'действие', 'ответ']:
                continue
            if line.lower().startswith('думаю:'):
                continue
            if line.lower().startswith('действие:'):
                continue
            if line.lower().startswith('final_answer'):
                continue
            if line.lower().startswith('ответ:'):
                continue

            result_lines.append(line)

        # Join cleaned lines and remove any remaining duplicates
        clean_answer = '\n'.join(result_lines).strip()

        # If still contains FINAL_ANSWER marker, extract text after it
        if 'final_answer' in clean_answer.lower():
            parts = clean_answer.lower().split('final_answer')
            if len(parts) > 1:
                clean_answer = parts[-1].strip()

        # Format based on whether tools were used
        if tool_history:
            # Build summary of tool usage
            tools_used = {}
            for call in tool_history:
                tool_name = call.get('tool', 'Unknown')
                tools_used[tool_name] = tools_used.get(tool_name, 0) + 1

            # Format tools summary
            tools_summary = "\n\n📋 **Использованные инструменты:**\n"
            for tool_name, count in tools_used.items():
                if tool_name == "CALENDAR":
                    tools_summary += f"📅 Календарь ({count})"
                elif tool_name == "WEBSEARCH":
                    tools_summary += f"🔍 Веб-поиск ({count})"
                else:
                    tools_summary += f"🔧 {tool_name} ({count})"
                tools_summary += "\n"

            # Add the main answer with proper formatting
            final_response = f"✅ **Результат:**\n\n{clean_answer}"
        else:
            # No tools used, just clean answer
            final_response = f"💬 **Ответ:**\n\n{clean_answer}"

        return final_response

    async def _execute_tool(self, tool_name: str, tool_input: str) -> str:
        """Execute the specified tool."""
        try:
            if tool_name == "CALENDAR":
                import re

                # Check if it's a task creation request
                if "создать_задачу" in tool_input.lower() or "create_task" in tool_input.lower():
                    # Parse task creation parameters using new pipe-separated format
                    user_id = "user-1"  # Default user ID
                    title = ""
                    date = ""
                    time = ""
                    description = ""

                    # New format: параметр | параметр | параметр
                    # Extract parameters using pipe separator
                    title_match = re.search(r'название\s*:\s*([^\]|]+?)(?:\]|\||$)', tool_input, re.IGNORECASE)
                    if title_match:
                        title = title_match.group(1).strip()

                    date_match = re.search(r'дата\s*:\s*(\d{4}-\d{2}-\d{2})', tool_input, re.IGNORECASE)
                    if date_match:
                        date = date_match.group(1).strip()

                    time_match = re.search(r'время\s*:\s*(\d{2}:\d{2})', tool_input, re.IGNORECASE)
                    if time_match:
                        time = time_match.group(1).strip()

                    desc_match = re.search(r'описание\s*:\s*([^\]|]+?)(?:\]|\||$)', tool_input, re.IGNORECASE)
                    if desc_match:
                        description = desc_match.group(1).strip()

                    if not title or not date or not time:
                        return f"Ошибка: недостаточно информации для создания задачи.\nТребуется: название, дата (YYYY-MM-DD), время (HH:MM)\nПолучено: название='{title}', дата='{date}', время='{time}'"

                    result = await CalendarTool.create_task(user_id, title, date, time, description)

                elif "получить_задачи" in tool_input.lower() or "get_tasks" in tool_input.lower():
                    # Parse date range parameters
                    user_id = "user-1"
                    start_date = ""
                    end_date = ""

                    # Extract date range
                    start_match = re.search(r'начало\s*:\s*(\d{4}-\d{2}-\d{2})', tool_input, re.IGNORECASE)
                    if start_match:
                        start_date = start_match.group(1).strip()

                    end_match = re.search(r'конец\s*:\s*(\d{4}-\d{2}-\d{2})', tool_input, re.IGNORECASE)
                    if end_match:
                        end_date = end_match.group(1).strip()

                    if not start_date or not end_date:
                        return f"Ошибка: требуется указать диапазон дат (начало и конец в формате YYYY-MM-DD)"

                    # Get tasks in date range
                    result = await CalendarTool.get_tasks_in_range(user_id, start_date, end_date)

                else:
                    # Parse calendar parameters for other actions
                    action = "current_date"
                    days_offset = 0
                    task_description = None

                    if "add_days" in tool_input.lower():
                        action = "add_days"
                        # Extract days from input
                        match = re.search(r'дн[ей]*[:\s]+(\d+)', tool_input)
                        if match:
                            days_offset = int(match.group(1))

                    elif "timeline" in tool_input.lower() or "график" in tool_input.lower():
                        action = "timeline_suggestion"
                        # Extract task description
                        match = re.search(r'задач[ау][:\s]+(.+)', tool_input)
                        if match:
                            task_description = match.group(1).strip()

                    elif "текущая_дата" in tool_input.lower() or "current_date" in tool_input.lower():
                        action = "current_date"

                    result = await CalendarTool.execute(action, days_offset, task_description)

            elif tool_name == "WEBSEARCH":
                # Parse search parameters
                query = tool_input
                max_results = 5

                import re
                # Try to extract query and max_results
                match = re.search(r'запрос[:\s]+(.+?)(?:,|$)', tool_input)
                if match:
                    query = match.group(1).strip()

                match = re.search(r'результ[ов]*[:\s]+(\d+)', tool_input)
                if match:
                    max_results = int(match.group(1))

                result = await WebSearchTool.execute(query, max_results)

            else:
                result = {"success": False, "error": f"Unknown tool: {tool_name}"}

            if result.get("success"):
                return json.dumps(result, ensure_ascii=False)
            else:
                return f"Ошибка инструмента: {result.get('error', 'Unknown error')}"

        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return f"Ошибка при выполнении инструмента: {str(e)}"
