# chat.py
import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse, ConversationState
from app.services.troubleshoot import TroubleshootService

logger = logging.getLogger(__name__)

# ChatSession class for session state
class ChatSession:
    def __init__(self):
        self.state = ConversationState.GREETING
        self.issue_description = ""
        self.auto_test_results = None
        self.follow_up_questions = []
        self.current_question_index = 0
        self.user_answers = []

router = APIRouter()
sessions = {}

# Initialize service lazily to ensure environment variables are loaded
def get_troubleshoot_service():
    return TroubleshootService()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id
    user_message = request.message

    logger.info(f"Received chat request - session: {session_id}, message: {user_message}")
    
    if session_id not in sessions:
        service = get_troubleshoot_service()
        sessions[session_id] = service.initialize_session()
        logger.info(f"Created new session: {session_id}")

    session = sessions[session_id]
    logger.info(f"SESSION DEBUG: id={session_id}, state={session.state}, idx={session.current_question_index}, answers={session.user_answers}, followups={session.follow_up_questions}")
    logger.info(f"Session {session_id} state: {session.state}")

    if session.state == ConversationState.GREETING:
        session.issue_description = user_message
        session.state = ConversationState.RUN_AUTO_TESTS
        return ChatResponse(message="Got it. Running a quick test on your network...")

    elif session.state == ConversationState.RUN_AUTO_TESTS:
        # Store actual test results from frontend
        session.auto_test_results = request.auto_test_results
        logger.info(f"Processing auto test results for session {session_id}")
        
        # Format test results using centralized method
        service = get_troubleshoot_service()
        formatted_results = service.format_test_results(session.auto_test_results)
        logger.debug(f"Formatted test results: {formatted_results}")
        
        results_message = (
    f"📊 **Test Results**  \n"
    f"• **Speed:** {formatted_results['speed']} Mbps  \n"
    f"• **Latency:** {formatted_results['latency']} ms  \n"
    f"• **Connection Type:** {formatted_results['connection_type']}  \n"
    f"• **Connectivity:** {'✅ Working' if formatted_results.get('connectivity_status', True) else '❌ Issues detected'}  \n"
    f"Based on these results, let me ask you a few questions to better understand the issue."
)
        
        # Generate first follow-up question
        service = get_troubleshoot_service()
        question = await service.generate_next_question(
            session.issue_description,
            session.auto_test_results,
            session.user_answers,
            0,  # question_number
            session.follow_up_questions
        )
        
        session.follow_up_questions.append(question)
        session.state = ConversationState.FOLLOW_UP_QUESTIONS
        logger.info(f"Generated first follow-up question for session {session_id}")
        return ChatResponse(message=f"{results_message}\n\n{question}")

    elif session.state == ConversationState.FOLLOW_UP_QUESTIONS:
        # Save the current answer before generating next question
        if session.current_question_index < len(session.user_answers):
            # We already have an answer for this question, update it
            session.user_answers[session.current_question_index] = user_message
        else:
            # First time answering this question
            session.user_answers.append(user_message)
        
        logger.info(f"Current question progress - index: {session.current_question_index}, total answers: {len(session.user_answers)}")

        # Check if we've asked enough questions (max 5)
        if session.current_question_index >= 4:  # 0-indexed, so 5 questions total
            service = get_troubleshoot_service()
            conclusion = await service.generate_conclusion(session)
            session.state = ConversationState.POST_REBOOT_CHECK
            return ChatResponse(message=conclusion)
        
        # Generate next question
        service = get_troubleshoot_service()
        question = await service.generate_next_question(
            session.issue_description,
            session.auto_test_results,
            session.user_answers,
            session.current_question_index,
            session.follow_up_questions
        )
        
        # Only increment the question index after we've processed the current answer
        session.current_question_index += 1
        
        # Store the next question
        if len(session.follow_up_questions) <= session.current_question_index:
            session.follow_up_questions.append(question)
        else:
            session.follow_up_questions[session.current_question_index] = question
            
        logger.info(f"Generated follow-up question {session.current_question_index + 1} for session {session_id}")
        return ChatResponse(message=question)

    elif session.state == ConversationState.SOLUTION_ANALYSIS:
        logger.info(f"Analyzing solution for session {session_id}")
        # Check if user indicated the issue is resolved
        service = get_troubleshoot_service()
        if service.is_issue_resolved(user_message):
            logger.info(f"Issue resolved for session {session_id}")
            return ChatResponse(message=service.get_success_message())
        
        # Check if reboot is needed
        service = get_troubleshoot_service()
        should_reboot = await service.should_reboot_router(
            session.auto_test_results,
            session.user_answers
        )

        session.state = ConversationState.POST_REBOOT_CHECK
        return ChatResponse(message="Based on your test results, I recommend rebooting your router. Please unplug your router, wait 30 seconds, then plug it back in. After 2-3 minutes, test your connection.")



    elif session.state == ConversationState.POST_REBOOT_CHECK:
        logger.info(f"Post reboot check for session {session_id}")
        service = get_troubleshoot_service()
        if service.is_issue_resolved(user_message):
            logger.info(f"Issue resolved after reboot for session {session_id}")
            session.state = ConversationState.CONVERSATION_END
            return ChatResponse(message=service.get_success_message(), is_conversation_ended=True)
        else:
            logger.info(f"Issue not resolved after reboot for session {session_id}")
            session.state = ConversationState.CONVERSATION_END
            return ChatResponse(message=service.get_support_message(), is_conversation_ended=True)

    elif session.state == ConversationState.CONVERSATION_END:
        service = get_troubleshoot_service()
        return ChatResponse(message=service.get_ending_message(), is_conversation_ended=True)

    else:
        logger.error(f"Unknown conversation state for session {session_id}: {session.state}")
        raise HTTPException(status_code=400, detail="Unknown conversation state.")
