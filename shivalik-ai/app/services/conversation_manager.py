
from collections import defaultdict, deque
from threading import Lock
from uuid import uuid4


class ConversationManager:
    def __init__(self, max_turns: int = 5):
        self.max_messages = max_turns * 2
        self.sessions = defaultdict(
            lambda: deque(maxlen=self.max_messages)
        )
        self.lock = Lock()

    def create_session(self) -> str:
        session_id = str(uuid4())

        with self.lock:
            self.sessions[session_id] = deque(
                maxlen=self.max_messages
            )

        return session_id

    def get_history(self, session_id: str) -> list[dict]:
        with self.lock:
            return list(self.sessions.get(session_id, []))

    def add_turn(
        self,
        session_id: str,
        question: str,
        answer: str
    ) -> None:
        with self.lock:
            if session_id not in self.sessions:
                raise ValueError("Unknown conversation session")

            self.sessions[session_id].append({
                "role": "user",
                "content": question
            })

            self.sessions[session_id].append({
                "role": "assistant",
                "content": answer
            })

    def delete_session(self, session_id: str) -> None:
        with self.lock:
            self.sessions.pop(session_id, None)


conversation_manager = ConversationManager(max_turns=5)
