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
    
    async def is_input_valid(self, user_input: str, question: str) -> bool:
        """
        Use LLM to validate if user input appropriately answers the question.
        Returns True if valid, False if invalid.
        """
        if not user_input or not user_input.strip():
            return False
        
        validation_prompt = f"""Question: "{question}"
User response: "{user_input}"

Does the user's response appropriately answer the question? Consider variations and be reasonably lenient.

Answer only: YES or NO"""

        try:
            response = await self.llm.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": validation_prompt}
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            result = response.choices[0].message.content.strip().upper()
            logger.info(f"Input validation result: {result}")
            return "YES" in result
                
        except Exception as e:
            logger.error(f"Error during input validation: {e}")
            # If validation fails, assume input is valid to avoid blocking user
            return True

    async def generate_next_question(
        self,
        issue_description: str,
        test_results: AutoTestResults,
        user_answers: list[str],
        question_number: int,
        follow_up_questions: list[str],
        previous_question: str | None = None,
        user_input: str | None = None,
        last_question: str | None = None,
    ) -> str:
        
        logger.info(f"Generating question {question_number + 1} for issue: {issue_description}")
        logger.debug(f"Test results: {test_results}, User answers: {user_answers}")
        
        # Derive missing context from existing lists if not provided explicitly
        if previous_question is None and follow_up_questions:
            previous_question = follow_up_questions[-1]
        if user_input is None and user_answers:
            user_input = user_answers[-1]
        if last_question is None:
            last_question = previous_question

        # Validate user input if we have a previous question and user response
        if previous_question and user_input is not None:
            is_valid = await self.is_input_valid(user_input, previous_question)
            
            if not is_valid:
                logger.info(f"Invalid user input detected: {user_input}. Re-asking question.")
                return last_question or previous_question
        
        # Build prior Q/A pairs correctly by pairing asked questions with their answers
        previous_context = "  \n".join(
            f"Q{i+1}: {q}\nA{i+1}: {a}"
            for i, (q, a) in enumerate(zip(follow_up_questions, user_answers))
        ) if user_answers and follow_up_questions else ""

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
        system_prompt = f"""
You are a WiFi troubleshooting expert. Your role is to diagnose the user's WiFi issue by asking **ONE** question at a time, progressing from the most common causes to the least common.

User's Issue: {issue_description}
{test_summary}
{previous_context}
Previous questions: {previous_questions}
This is question #{question_number+1}.

**Your core objectives:**
- Review the previous questions already asked
- Ask ONLY **one** clear, specific, and actionable troubleshooting question at a time.
- Base each question on the test results, previous answers, and remaining unexplored categories.
- Progress logically: start with the most common potential issues before moving to rarer ones.

**Handling invalid or unhelpful responses:**
- If the user gives an irrelevant, nonsense, evasive, or incomplete answer, **ask the same question again but in a different way** (simpler words, more context, or examples).
- If they refuse to answer, reframe the question so it’s easier or more appealing to answer.
- Keep re-asking in alternative forms until you receive a valid, useful answer.
- Only move to a new topic when you have enough information about the current one.

**Question Categories (reference order):**
1. Network congestion & bandwidth usage  
2. Physical connection & hardware issues  
3. Router/Modem configuration & status  
4. Signal strength & interference  
5. Device-specific issues  

**Important final step:**
- Once you’ve gathered enough information, provide a **specific technical conclusion**.
- If a reboot is required, end your last response **exactly** with:  
  `Did the reboot improve your connection? (Yes/No)`  
- Do **not** add any text after this Yes/No question.

Now, ask ONLY the **next** troubleshooting question — or, if ready, give the final conclusion with the reboot question.
"""


        response = await self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
            ],
            temperature=0.0
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