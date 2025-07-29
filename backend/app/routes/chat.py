from fastapi import APIRouter, HTTPException
from typing import Dict
from app.models.schemas import (
    ChatRequest, ChatResponse, ConversationState, 
    UserSymptoms, ChatMessage, SessionData, AutoTestResults
)
from app.services.troubleshoot import WiFiTroubleshootService

router = APIRouter()

# In-memory session storage (use Redis in production)
sessions: Dict[str, SessionData] = {}

troubleshoot_service = WiFiTroubleshootService()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Linear chat endpoint: greet, show test results, ask questions, provide suggestion."""
    # Get or create session
    if request.session_id not in sessions:
        sessions[request.session_id] = SessionData(
            session_id=request.session_id,
            state=ConversationState.GREETING,
            symptoms=UserSymptoms(),
            conversation_history=[],
            current_question_index=0
        )
    session = sessions[request.session_id]

    # Add user message to history
    user_message = ChatMessage(role="user", content=request.message)
    session.conversation_history.append(user_message)

    response_message = ""
    next_question = None
    is_conversation_ended = False
    current_question_number = None
    total_questions = 4  # 1 test + 3 follow-ups
    reboot_recommended = False
    solution_analysis = {}

    if session.state == ConversationState.GREETING:
        response_message = "Hi! I'll help you troubleshoot your WiFi. I'll run a quick test, show you the results, then ask a few follow-up questions before giving you a suggestion."
        session.state = ConversationState.AUTO_TESTING
        next_question = "Running automatic connection test..."

    elif session.state == ConversationState.AUTO_TESTING:
        if request.auto_test_results:
            session.symptoms.auto_test_results = request.auto_test_results
            response_message = troubleshoot_service.format_test_results(request.auto_test_results)
            session.state = ConversationState.TARGETED_QUESTIONS
            session.current_question_index = 0
            session.user_answers = []
            next_question = await troubleshoot_service.generate_ai_question(
                1, None, request.auto_test_results, []
            )
            current_question_number = 1
        else:
            response_message = "Waiting for automatic test results..."
            next_question = None

    elif session.state == ConversationState.TARGETED_QUESTIONS:
        # Store answer
        if not hasattr(session, "user_answers"):
            session.user_answers = []
        # Check if more follow-up questions should be asked (assume 3 questions in linear flow)
        if session.current_question_index < 3:
            # Ask next follow-up
            next_question = await troubleshoot_service.generate_ai_question(
                session.current_question_index + 1, None, session.symptoms.auto_test_results, session.user_answers
            )
            response_message = next_question
            session.current_question_index += 1
            current_question_number = session.current_question_index + 1
        else:
            # Proceed to final suggestion
            session.state = ConversationState.SOLUTION_ANALYSIS
            response_message = await troubleshoot_service.generate_final_suggestion(
                session.symptoms.auto_test_results, session.user_answers
            )
            is_conversation_ended = True

        # Get AI response acknowledging the answer
        response_message = await troubleshoot_service.get_openai_response(
            request.message, session.state, session.symptoms, 
            context=f"Question {session.current_question_index + 1} of 5"
        )

        # Move to next question or analysis
        session.current_question_index += 1
        current_question_number = session.current_question_index + 1

    elif session.state == ConversationState.SOLUTION_ANALYSIS:
        # Perform combined analysis
        solution_analysis = troubleshoot_service.analyze_combined_results(session.symptoms)
        reboot_recommended = solution_analysis["reboot_recommended"]
        
        if reboot_recommended:
            response_message += f"\n\n📊 **Analysis Complete!**\n"
            response_message += f"**Confidence:** {solution_analysis['confidence'].title()}\n"
            response_message += f"**Reasoning:** {', '.join(solution_analysis['reasoning'])}\n\n"
            response_message += f"**Recommendation:** Router reboot should resolve your issues!\n\n"
            response_message += troubleshoot_service.get_reboot_instructions()
            session.state = ConversationState.REBOOT_INSTRUCTIONS
            next_question = "Let me know when you've completed the reboot steps!"
        if session.current_question_index < len(questions):
            # Ask next targeted question
            next_q = questions[session.current_question_index]
            next_question = next_q["question"]
        else:
            # All 5 questions asked, analyze results
            session.state = ConversationState.SOLUTION_ANALYSIS
            
            # Perform combined analysis
            solution_analysis = troubleshoot_service.analyze_combined_results(session.symptoms)
            reboot_recommended = solution_analysis["reboot_recommended"]
            
            if reboot_recommended:
                response_message += f"\n\n📊 **Analysis Complete!**\n"
                response_message += f"**Confidence:** {solution_analysis['confidence'].title()}\n"
                response_message += f"**Reasoning:** {', '.join(solution_analysis['reasoning'])}\n\n"
                response_message += f"**Recommendation:** Router reboot should resolve your issues!\n\n"
                response_message += troubleshoot_service.get_reboot_instructions()
                session.state = ConversationState.REBOOT_INSTRUCTIONS
                next_question = "Let me know when you've completed the reboot steps!"
            else:
                response_message += f"\n\n📊 **Analysis Complete!**\n"
                response_message += f"Based on your test results and answers, a simple router reboot may not solve this issue.\n\n"
                response_message += f"**Alternative solutions to try:**\n"
                for i, solution in enumerate(solution_analysis["alternative_solutions"], 1):
                    response_message += f"{i}. {solution}\n"
                session.state = ConversationState.ESCALATION
                is_conversation_ended = True
                
    elif session.state == ConversationState.REBOOT_INSTRUCTIONS:
        response_message = "Perfect! Now let's check if the reboot fixed your WiFi issue."
        next_question = "Are you now able to connect to your WiFi and browse the internet normally?"
        session.state = ConversationState.POST_REBOOT_CHECK
        
    elif session.state == ConversationState.POST_REBOOT_CHECK:
        if any(word in request.message.lower() for word in ["yes", "working", "fixed", "good", "better"]):
            response_message = "🎉 Excellent! I'm glad the router reboot solved your WiFi problem.\n\n"
            response_message += "**Pro tip:** Rebooting your router once a week can prevent many connectivity issues.\n\n"
            response_message += "Thanks for using the WiFi troubleshooter!"
            session.state = ConversationState.RESOLVED
            is_conversation_ended = True
        else:
            response_message = "😔 I'm sorry the reboot didn't resolve your WiFi issue.\n\n"
            response_message += "Since the basic troubleshooting didn't work, you may need to:\n"
            response_message += "• Contact your internet service provider\n"
            response_message += "• Check if there are service outages in your area\n"
            response_message += "• Consider if your router hardware needs replacement\n\n"
            response_message += "Thanks for trying the troubleshooting steps!"
            session.state = ConversationState.ESCALATION
            is_conversation_ended = True
    
    # Add bot response to history
    bot_message = ChatMessage(role="assistant", content=response_message)
    session.conversation_history.append(bot_message)
    
    # Update session
    sessions[request.session_id] = session
    
    return ChatResponse(
        message=response_message,
        state=session.state,
        symptoms=session.symptoms,
        conversation_history=session.conversation_history,
        next_question=next_question,
        is_conversation_ended=is_conversation_ended,
        reboot_recommended=reboot_recommended,
        solution_analysis=solution_analysis,
        current_question_number=current_question_number,
        total_questions=total_questions
    )

@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a session"""
    if session_id in sessions:
        del sessions[session_id]
        return {"message": "Session cleared"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session data"""
    if session_id in sessions:
        return sessions[session_id]
    else:
        raise HTTPException(status_code=404, detail="Session not found")