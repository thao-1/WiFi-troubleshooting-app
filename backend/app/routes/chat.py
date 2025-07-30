# chat.py
import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse, ConversationState
from app.services.troubleshoot import TroubleshootService

logger = logging.getLogger(__name__)

# Minimal ChatSession class for session state
class ChatSession:
    def __init__(self):
        self.state = ConversationState.GREETING
        self.issue_description = ""
        self.auto_test_results = None
        self.follow_up_questions = []
        self.current_question_index = 0
        self.user_answers = []

router = APIRouter()
troubleshoot_service = TroubleshootService()
sessions = {}

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id
    user_message = request.message

    logger.info(f"Received chat request - session: {session_id}, message: {user_message}")
    
    if session_id not in sessions:
        sessions[session_id] = troubleshoot_service.initialize_session()
        logger.info(f"Created new session: {session_id}")

    session = sessions[session_id]
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
        formatted_results = troubleshoot_service.format_test_results(session.auto_test_results)
        logger.debug(f"Formatted test results: {formatted_results}")
        
        results_message = (
            f"📊 **Test Results:**\n"
            f"• **Speed:** {formatted_results['speed']} Mbps\n"
            f"• **Latency:** {formatted_results['latency']} ms\n"
            f"• **Connection Type:** {formatted_results['connection_type']}\n"
            f"• **Connectivity:** {'✅ Working' if formatted_results.get('connectivity_status', True) else '❌ Issues detected'}\n\n"
            f"Based on these results, let me ask you a few questions to better understand the issue."
        )
        
        # Generate first follow-up question
        question = await troubleshoot_service.generate_next_question(
            session.issue_description,
            session.auto_test_results,
            session.user_answers,
            0
        )
        
        session.follow_up_questions.append(question)
        session.state = ConversationState.FOLLOW_UP_QUESTIONS
        logger.info(f"Generated first follow-up question for session {session_id}")
        return ChatResponse(message=f"{results_message}\n\n{question}")

    elif session.state == ConversationState.FOLLOW_UP_QUESTIONS:
        if session.current_question_index < len(session.follow_up_questions):
            # Save previous answer
            if session.current_question_index > 0:
                session.user_answers.append(user_message)

            # Check if we've asked enough questions (max 5)
            if session.current_question_index >= 4:  # 0-indexed, so 5 questions total
                # Generate intelligent conclusion with reboot recommendation
                conclusion = await troubleshoot_service.generate_conclusion(session)
                session.state = ConversationState.POST_REBOOT_CHECK
                return ChatResponse(message=conclusion)
            else:
                question = await troubleshoot_service.generate_next_question(
                    session.issue_description,
                    session.auto_test_results,
                    session.user_answers,
                    session.current_question_index
                )

                session.follow_up_questions.append(question)
                session.current_question_index += 1
                logger.info(f"Generated follow-up question {session.current_question_index} for session {session_id}")
                return ChatResponse(message=question)
        else:
            session.user_answers.append(user_message)
            session.state = ConversationState.SOLUTION_ANALYSIS
            return ChatResponse(message="Thanks! Analyzing everything now...")

    elif session.state == ConversationState.SOLUTION_ANALYSIS:
        logger.info(f"Analyzing solution for session {session_id}")
        # Check if user indicated the issue is resolved
        if troubleshoot_service.is_issue_resolved(user_message):
            logger.info(f"Issue resolved for session {session_id}")
            return ChatResponse(message=troubleshoot_service.get_success_message())
        
        # Check if reboot is needed
        should_reboot = await troubleshoot_service.should_reboot_router(
            session.auto_test_results,
            session.user_answers
        )

        session.state = ConversationState.POST_REBOOT_CHECK
        return ChatResponse(message="Based on your test results, I recommend rebooting your router. Please unplug your router, wait 30 seconds, then plug it back in. After 2-3 minutes, test your connection.")



    elif session.state == ConversationState.POST_REBOOT_CHECK:
        logger.info(f"Post reboot check for session {session_id}")
        if troubleshoot_service.is_issue_resolved(user_message):
            logger.info(f"Issue resolved after reboot for session {session_id}")
            session.state = ConversationState.CONVERSATION_END
            return ChatResponse(message=troubleshoot_service.get_success_message())
        else:
            logger.info(f"Issue not resolved after reboot for session {session_id}")
            session.state = ConversationState.CONVERSATION_END
            return ChatResponse(message=troubleshoot_service.get_support_message())

    elif session.state == ConversationState.CONVERSATION_END:
        return ChatResponse(message="This conversation has ended. Please start a new session if you need more help.")

    else:
        logger.error(f"Unknown conversation state for session {session_id}: {session.state}")
        raise HTTPException(status_code=400, detail="Unknown conversation state.")
