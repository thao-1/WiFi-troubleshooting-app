from bdb import effective
from turtle import st
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum

class ConversationState(str, Enum):
    GREETING = "greeting"
    AUTO_TESTING = "auto_testing"
    TARGETED_QUESTIONS = "targeted_questions"
    SOLUTION_ANALYSIS = "solution_analysis"
    REBOOT_INSTRUCTIONS = "reboot_instructions"
    POST_REBOOT_CHECK = "post_reboot_check"
    RESOLVED = "resolved"
    ESCALATION = "escalation"

class AutoTestResults(BaseModel):
    connectivity_status: bool
    speed_mbps: Optional[float] = None
    latency_ms: Optional[int] = None
    effective_connection_type: Optional[str] = None
    packet_loss: Optional[float] = None
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
    conversation_history: List[ChatMessage] = []
    auto_test_results: Optional[AutoTestResults] = None

class ChatResponse(BaseModel):
    message: str
    state: ConversationState
    symptons: UserSymptoms
    conversation_history: List[ChatMessage]
    next_question: Optional[str] = None
    is_conversation_ended: bool = False
    reboot_recommended: Optional[bool] = None
    solution_analysis: Optional[Dict[str, Any]] = None
    current_question_number: Optional[int] = None
    total_questions: Optional[int] = None

class SessionData(BaseModel):
    session_id: str
    state: ConversationState
    symptoms: UserSymptoms
    conversation_history: List[ChatMessage]
    current_question_index: int = 0
    question_path: str = "default"
