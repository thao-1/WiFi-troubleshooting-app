import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.routes.chat import sessions, ChatSession, ConversationState, get_troubleshoot_service

async def simulate_chat():
    session_id = "test_session"
    sessions[session_id] = ChatSession()
    session = sessions[session_id]

    # Step 1: User sends first message
    print("User: My WiFi is slow")
    session.issue_description = "My WiFi is slow"
    session.state = ConversationState.RUN_AUTO_TESTS
    print(f"State: {session.state}")

    # Step 2: Auto test results
    service = get_troubleshoot_service()
    session.auto_test_results = {"speed": {"speed": 5}, "latency": 100, "connectionInfo": {"type": "wifi"}, "connectivity": {"connected": True}, "deviceType": "laptop"}
    formatted_results = service.format_test_results(session.auto_test_results)
    session.follow_up_questions.append("Is your router plugged in?")
    session.state = ConversationState.FOLLOW_UP_QUESTIONS
    print(f"Bot: Test results: {formatted_results}")
    print(f"Bot: {session.follow_up_questions[-1]}")
    print(f"State: {session.state}")

    # Step 3: User answers follow-up question
    session.user_answers.append("Yes")
    session.current_question_index += 1
    if session.current_question_index >= 1:  # Simulate only 1 question for brevity
        session.state = ConversationState.SOLUTION_ANALYSIS
        print(f"Bot: Thanks! Analyzing everything now...")
        print(f"State: {session.state}")

    # Step 4: Solution analysis and reboot recommendation
    session.state = ConversationState.POST_REBOOT_CHECK
    print(f"Bot: Based on your test results, I recommend rebooting your router. Please unplug your router, wait 30 seconds, then plug it back in. After 2-3 minutes, test your connection.")
    print(f"State: {session.state}")

    # Step 5: User answers reboot question
    user_message = "Yes"
    if service.is_issue_resolved(user_message):
        session.state = ConversationState.CONVERSATION_END
        print(f"Bot: {service.get_success_message()}")
        print(f"State: {session.state}")
    else:
        session.state = ConversationState.CONVERSATION_END
        print(f"Bot: {service.get_support_message()}")
        print(f"State: {session.state}")

    # Step 6: Any further message
    if session.state == ConversationState.CONVERSATION_END:
        print("Bot: This conversation has ended. Please start a new session if you need more help.")

# Run the simulation
if __name__ == "__main__":
    asyncio.run(simulate_chat())
