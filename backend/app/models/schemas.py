from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from enum import Enum

class ConversationState(str, Enum):
    GREETING = "greeting"
    ASK_ISSUE = "ask_issue"
    RUN_AUTO_TESTS = "run_auto_tests"
    FOLLOW_UP_QUESTIONS = "follow_up_questions"
    SOLUTION_ANALYSIS = "solution_analysis"
    POST_REBOOT_CHECK = "post_reboot_check"
    CONVERSATION_END = "conversation_end"


class AutoTestResults(BaseModel):
    connectivity: Dict[str, Any] = {}
    speed: Dict[str, Any] = {}
    connectionInfo: Dict[str, Any] = {}
    deviceType: Optional[str] = None
    test_timestamp: Optional[str] = None

class UserSymptoms(BaseModel):
    # Auto-test results
    auto_test_results: Optional[AutoTestResults] = None
    # Traditional symptoms (from 5 questions)
    can_see_network: Optional[bool] = None
    can_connect: Optional[bool] = None
    multiple_devices_affected: Optional[bool] = None
    days_since_last_reboot: Optional[int] = None
    internet_completely_down: Optional[bool] = None
    slow_speeds: Optional[bool] = None
    intermittent_connection: Optional[bool] = None
    specific_websites_affected: Optional[bool] = None
    error_messages_seen: Optional[bool] = None
    router_lights_status: Optional[str] = None

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    session_id: str
    auto_test_results: Optional[AutoTestResults] = None

class ChatResponse(BaseModel):
    message: str
    next_question: Optional[str] = None
    is_conversation_ended: bool = False

class SessionData(BaseModel):
    session_id: str
    state: ConversationState
    symptoms: UserSymptoms
    conversation_history: List[ChatMessage]
    current_question_index: int = 0
    question_path: str = "default"
    user_answers: List[str] = []
