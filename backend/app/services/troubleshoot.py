# troubleshoot.py
import logging
import random
from app.models.schemas import AutoTestResults
import os
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class TroubleshootService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.llm = AsyncOpenAI(api_key=api_key)
        logger.info("TroubleshootService initialized with OpenAI client")

    def initialize_session(self):
        from app.routes.chat import ChatSession  
        return ChatSession()

    async def generate_next_question(
        self,
        issue_description: str,
        test_results: AutoTestResults,
        user_answers: list[str],
        question_number: int,
        follow_up_questions: list[str],
    ) -> str:
        
        logger.info(f"Generating question {question_number + 1} for issue: {issue_description}")
        logger.debug(f"Test results: {test_results}, User answers: {user_answers}")
        previous_context = "  \n".join(
            f"Q{i+1}: {q}\nA{i+1}: {a}" for i, (q, a) in enumerate(zip(user_answers[:-1], user_answers[1:]))
        ) if len(user_answers) > 1 else ""

        # Use centralized test results formatting
        formatted_results = self.format_test_results(test_results)
        
        test_summary = (
            f"Connectivity: {formatted_results['connectivity_status']}, "
            f"Speed: {formatted_results['speed']} Mbps, "
            f"Latency: {formatted_results['latency']} ms, "
            f"Connection Type: {formatted_results['connection_type']}, "
            f"Device Type: {formatted_results['device_type']}"
        )

        previous_questions = " | ".join(follow_up_questions)
        system_prompt = f"""You are a WiFi troubleshooting expert. Your job is to help diagnose the user's WiFi issue by asking ONE question at a time.

User's Issue: {issue_description}
{test_summary}
{previous_context}
Previous questions already asked: {previous_questions}
This is question #{question_number+1} out of 5.

**Your task:**
- Ask ONLY ONE clear, specific troubleshooting question.
- Each question must cover a DIFFERENT aspect of troubleshooting (hardware, software, configuration, environment, etc.)
- DO NOT repeat or rephrase previous questions listed above.
- If a question was already asked and answered, move to a different aspect.
- Questions should progress from most common to least common issues.
- Make each question specific and actionable.
- Consider the test results and previous answers when forming your question.

**Question Categories (for reference):**
1. Network congestion and bandwidth usage
2. Physical connection and hardware issues
3. Router/Modem configuration and status
4. Signal strength and interference
5. Device-specific issues

**Important Rules:**
- After 5 questions, provide a specific conclusion with clear reboot instructions if needed.
- If reboot is needed, your last response MUST end with: **"Did the reboot improve your connection? (Yes/No)"**
- DO NOT add any text after the Yes/No question in the conclusion.
- Be specific and technical in your recommendations.

Now ask ONLY the next question or finish with the final reboot instructions and Yes/No question:
"""

        response = await self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
            ],
            temperature=0.2
        )
        question = response.choices[0].message.content.strip()
        logger.info(f"Generated question: {question}")
        return question

    def format_test_results(self, test_results: AutoTestResults) -> dict:
        """Format test results into a consistent dictionary structure."""
        logger.debug(f"Formatting test results: {test_results}")
        if test_results is None:
            logger.warning("Test results are None, returning default values")
            return {
                'speed': 'unknown',
                'latency': 'unknown',
                'connection_type': 'unknown',
                'connectivity_status': False,
                'device_type': 'unknown'
            }
        # Handle both dict and object formats
        if hasattr(test_results, 'get'):  # dict format
            speed_data = test_results.get('speed', {})
            speed = speed_data.get('speed', 'unknown') if isinstance(speed_data, dict) else str(speed_data)
            
            latency_data = test_results.get('connectivity', {})
            latency = latency_data.get('latency', 'unknown') if isinstance(latency_data, dict) else str(latency_data)
            
            connection_data = test_results.get('connectionInfo', {})
            connection_type = connection_data.get('type', 'unknown') if isinstance(connection_data, dict) else str(connection_data)
            
            connectivity_data = test_results.get('connectivity', {})
            connectivity_status = connectivity_data.get('connected', False) if isinstance(connectivity_data, dict) else False
            
            device_type = test_results.get('deviceType', 'unknown')
        else:  # object format
            speed = getattr(test_results, 'speed', 'unknown')
            if hasattr(speed, 'speed'):
                speed = speed.speed
            
            latency = getattr(test_results, 'connectivity', 'unknown')
            if hasattr(latency, 'latency'):
                latency = latency.latency
            
            connection_type = getattr(test_results, 'connectionInfo', 'unknown')
            if hasattr(connection_type, 'type'):
                connection_type = connection_type.type
            
            connectivity_data = getattr(test_results, 'connectivity', {})
            connectivity_status = connectivity_data.get('connected', False) if hasattr(connectivity_data, 'get') else False
            
            device_type = getattr(test_results, 'deviceType', 'unknown')
        
        logger.debug(f"Formatted results: {{'speed': speed, 'latency': latency, 'connection_type': connection_type, 'connectivity_status': connectivity_status, 'device_type': device_type}}")
        return {
            'speed': speed,
            'latency': latency,
            'connection_type': connection_type,
            'connectivity_status': connectivity_status,
            'device_type': device_type
        }

    async def generate_conclusion(self, session):
        logger.info(f"Generating conclusion for session - issue: {session.issue_description}")
        logger.debug(f"User answers: {session.user_answers}, Test results: {session.auto_test_results}")
        # Generate intelligent conclusion based on test results and user answers."""
        formatted_results = self.format_test_results(session.auto_test_results)
        
        context = (
            f"Test Results: {formatted_results['speed']} Mbps speed, {formatted_results['latency']} ms latency, {formatted_results['connection_type']} connection\n"
            f"User Issue: {session.issue_description}\n"
            f"User Answers: {' | '.join(session.user_answers) if session.user_answers else 'No answers provided yet'}\n"
            f"Questions Asked: {session.current_question_index}\n"
        )
        
        prompt = f"""Based on these test results and user answers:
{context}

Provide a specific, personalized conclusion that:
1. Acknowledges the current status
2. Provides specific recommendations based on the actual data
3. Includes the reboot instructions if needed
4. Asks 1 last follow up question: "Did the reboot improve your connection? (Yes/No)
5. Be conversational and helpful

Format your answer using Markdown. Use `###` for section headings and `-` for bullet points. Make the analysis and recommendations intelligent and specific to this situation."""
        
        response = await self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a WiFi troubleshooting expert providing intelligent, personalized conclusions based on test results and user answers."},
                {"role": "user", "content": prompt}
            ]
        )
        
        conclusion = response.choices[0].message.content
        logger.info(f"Generated conclusion: {conclusion[:100]}...")
        return conclusion

    def is_issue_resolved(self, user_message: str) -> bool:
        """Check if user indicates the issue is resolved."""
        resolved = any(keyword in user_message.lower() for keyword in ['fine', 'works', 'fixed', 'yes', 'good', 'better', 'resolved', 'solved'])
        logger.info(f"Issue resolved check: {user_message} -> {resolved}")
        return resolved

    def get_success_message(self) -> str:
        """Get standardized success message."""
        return "🎉 I'm so glad I could help! Your WiFi issue appears to be resolved. If you experience any problems in the future, feel free to reach out. Have a great day!"

    def get_support_message(self) -> str:
        """Get standardized support message."""
        return "Sorry about that. Please call customer support at 888-888-8888 for further assistance."

    async def should_reboot_router(self, test_results: AutoTestResults, user_answers: list[str]) -> bool:
        logger.info(f"Checking if reboot should be recommended based on: {test_results}, {user_answers}")
        logger.debug(f"Test results: {test_results}, User answers: {user_answers}")
        # Handle both dict and object formats for test results
        if hasattr(test_results, 'get'):  # dict format
            speed = test_results.get('speed', {}).get('speed', 'unknown')
            latency = test_results.get('connectivity', {}).get('latency', 'unknown')
            connection_type = test_results.get('connectionInfo', {}).get('type', 'unknown')
            connectivity_status = "connected" if speed != 'unknown' else "disconnected"
            packet_loss = "0"
            device_type = "browser"
        else:  # object format
            speed = getattr(test_results, 'speed', 'unknown')
            if hasattr(speed, 'speed'):
                speed = speed.speed
            latency = getattr(test_results, 'connectivity', 'unknown')
            if hasattr(latency, 'latency'):
                latency = latency.latency
            connection_type = getattr(test_results, 'connectionInfo', 'unknown')
            if hasattr(connection_type, 'type'):
                connection_type = connection_type.type
            connectivity_status = "connected" if speed != 'unknown' else "disconnected"
            packet_loss = "0"
            device_type = "browser"

        context = (
            f"Connectivity: {connectivity_status}, "
            f"Speed: {speed} Mbps, "
            f"Latency: {latency} ms, "
            f"Connection Type: {connection_type}, "
            f"Packet Loss: {packet_loss}%, "
            f"Device Type: {device_type}\n\n"
            f"User Answers: {' | '.join(user_answers)}"
        )

        prompt = f"""You are a diagnostic AI. Based on this data:

{context}

Should the user try rebooting the router? Answer only YES or NO."""

        response = await self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": prompt},
            ],
            temperature=0.2
        )

        answer = response.choices[0].message.content.strip().lower()
        return "yes" in answer

    def get_ending_message(self) -> str:
        """Get standardized conversation end message."""
        return "This conversation has ended. Please start a new session if you need more help."