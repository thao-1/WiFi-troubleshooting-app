import openai
from typing import List, Dict, Optional, Tuple, Any
from app.models.schemas import (
    ConversationState, UserSymptoms, ChatMessage, SessionData, AutoTestResults
)
from app.core.config import settings

openai.api_key = settings.openai_api_key

class WiFiTroubleshootService:
    def __init__(self):
        # Predefined issue categories for initial selection
        self.issue_categories = {
            "slow_wifi": "My WiFi is slow",
            "cant_connect": "I can't connect to WiFi", 
            "intermittent": "My WiFi keeps disconnecting"
        }
        
        # Example question types for AI to reference
        self.question_examples = """
        Example question types you can ask:
        - Yes/No questions: "Can you see your WiFi network name in available networks?"
        - Multiple choice: "What color are the router lights? (Green/Red/Orange/Blinking)"
        - Number questions: "How many days since you last restarted your router?"
        - Descriptive: "What error messages do you see when trying to connect?"
        - Comparison: "Are other devices in your home having the same issue?"
        """

    def determine_question_path(self, issue_category: str, auto_test_results: Optional[AutoTestResults]) -> str:
        """Determine question focus based on user's initial selection and test results"""
        if issue_category == "slow_wifi":
            return "slow_speed"
        elif issue_category == "cant_connect":
            return "no_connectivity"
        elif issue_category == "intermittent":
            return "intermittent_connection"
        else:
            return "general_troubleshooting"

    async def generate_ai_question(self, question_number: int, issue_category: str, 
                                 auto_test_results: Optional[AutoTestResults], 
                                 previous_answers: List[str] = None) -> str:
        """Generate contextual questions using AI based on issue type and test results"""
        
        # Build context for AI
        test_summary = ""
        if auto_test_results:
            test_summary = f"""
            Connection Test Results:
            - Internet Connected: {auto_test_results.connectivity_status}
            - Speed: {auto_test_results.speed_mbps if auto_test_results.speed_mbps else 'Unknown'} Mbps
            - Response Time: {auto_test_results.latency_ms if auto_test_results.latency_ms else 'Unknown'} ms
            """
        
        previous_context = f"Previous answers: {', '.join(previous_answers)}" if previous_answers else "No previous answers yet"
        
        system_prompt = f"""You are a WiFi troubleshooting expert. You will generate 3-5 follow-up questions one at a time to diagnose the user's WiFi issue. Generate ONE question now and wait for their answer before the next question.

        User's Issue: {self.issue_categories.get(issue_category, 'General WiFi problem')}
        {test_summary}
        {previous_context}

        This is question #{question_number} of 3-5 total questions.

        Requirements:
        - Ask only ONE clear, specific question right now
        - Focus on gathering information that helps diagnose the root cause  
        - Make it conversational and easy to understand
        - Don't repeat information already gathered
        - Use the test results to guide your question
        - After 3-5 questions, you will provide the final solution based on the test summary and user answers

        Generate the next logical troubleshooting question:"""

        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate question {question_number} for {issue_category} issue"}
                ],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            # Fallback questions if AI fails
            fallback_questions = [
                "Are other devices in your home having the same WiFi problem?",
                "How many days has it been since you last restarted your router?",
                "What happens when you try to connect - do you get any error messages?",
                "Is this problem happening all the time or only sometimes?",
                "Is there anything specific about your WiFi setup you'd like me to know?"
            ]
            return fallback_questions[min(question_number - 1, len(fallback_questions) - 1)]

    async def generate_final_solution(self, issue_category: str, auto_test_results: Optional[AutoTestResults], 
                                    user_answers: List[str]) -> str:
        """Generate final solution based on test results and user answers"""
        
        test_summary = ""
        if auto_test_results:
            test_summary = f"""
            Connection Test Results:
            - Internet Connected: {auto_test_results.connectivity_status}
            - Speed: {auto_test_results.speed_mbps if auto_test_results.speed_mbps else 'Unknown'} Mbps
            - Response Time: {auto_test_results.latency_ms if auto_test_results.latency_ms else 'Unknown'} ms
            """
        
        system_prompt = f"""You are a WiFi troubleshooting expert. Provide a clear solution based on the test results and user answers.

        User's Issue: {self.issue_categories.get(issue_category, 'General WiFi problem')}
        {test_summary}
        User's Answers: {', '.join(user_answers) if user_answers else 'No additional answers'}
        
        Requirements:
        - Start with: "Based on your connectivity test and your answers, you should..."
        - Provide specific, actionable steps
        - Prioritize the most likely solution first
        - Keep it clear and easy to follow
        - Include why this solution addresses their specific issue
        
        Generate the troubleshooting solution:"""

        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate the solution"}
                ],
                max_tokens=300,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return "Based on your connectivity test and your answers, you should try restarting your router by unplugging it for 30 seconds, then plugging it back in. This resolves most common WiFi issues."

    def analyze_combined_results(self, symptoms: UserSymptoms) -> Dict[str, Any]:
        """Combine auto-test results with user answers to determine solution"""
        analysis = {
            "reboot_score": 0,
            "reboot_recommended": False,
            "confidence": "medium",
            "primary_issue": "unknown",
            "reasoning": [],
            "alternative_solutions": []
        }

        # Analyze auto-test results
        if symptoms.auto_test_results:
            auto_results = symptoms.auto_test_results
            
            if not auto_results.connectivity_status:
                analysis["reboot_score"] += 4
                analysis["primary_issue"] = "no_connectivity"
                analysis["reasoning"].append("Auto-test shows no internet connection")
            
            if auto_results.speed_mbps and auto_results.speed_mbps < 1:
                analysis["reboot_score"] += 3
                analysis["primary_issue"] = "slow_speed"
                analysis["reasoning"].append(f"Very slow speed detected: {auto_results.speed_mbps:.1f} Mbps")
            
            if auto_results.latency_ms and auto_results.latency_ms > 1000:
                analysis["reboot_score"] += 2
                analysis["reasoning"].append(f"High latency detected: {auto_results.latency_ms}ms")

        # Analyze user responses
        if symptoms.multiple_devices_affected:
            analysis["reboot_score"] += 3
            analysis["reasoning"].append("Multiple devices affected - likely router issue")
        
        if symptoms.days_since_last_reboot and symptoms.days_since_last_reboot >= 7:
            analysis["reboot_score"] += 2
            analysis["reasoning"].append(f"Router hasn't been rebooted in {symptoms.days_since_last_reboot} days")
        
        if not symptoms.can_see_network:
            analysis["reboot_score"] += 3
            analysis["reasoning"].append("Cannot see WiFi network")
        
        if not symptoms.can_connect:
            analysis["reboot_score"] += 2
            analysis["reasoning"].append("Cannot connect to WiFi network")

        # Determine recommendation
        if analysis["reboot_score"] >= 6:
            analysis["reboot_recommended"] = True
            analysis["confidence"] = "high"
        elif analysis["reboot_score"] >= 4:
            analysis["reboot_recommended"] = True
            analysis["confidence"] = "medium"
        else:
            analysis["reboot_recommended"] = False
            analysis["alternative_solutions"] = [
                "Contact your internet service provider",
                "Check for service outages in your area",
                "Update device WiFi drivers",
                "Check router placement and interference"
            ]

        return analysis

    async def get_openai_response(self, user_input: str, state: ConversationState, symptoms: UserSymptoms, context: str = "") -> str:
        """Get contextual response from OpenAI"""
        
        if state == ConversationState.GREETING:
            system_prompt = """You are a helpful WiFi troubleshooting assistant. 
            Acknowledge the user's WiFi problem warmly and explain that you'll run automatic tests first, 
            then ask targeted questions to find the best solution. Keep it conversational and reassuring."""
            
        elif state == ConversationState.AUTO_TESTING:
            system_prompt = """You are explaining auto-test results to a user. 
            Be clear about what the tests found and what it means for their WiFi problem. 
            Mention that you'll now ask some targeted questions to get the full picture."""
            
        elif state == ConversationState.TARGETED_QUESTIONS:
            system_prompt = f"""You are asking targeted WiFi troubleshooting questions. 
            The user just answered: "{user_input}"
            Context: {context}
            
            Acknowledge their answer briefly and naturally. Be conversational and empathetic."""
            
        elif state == ConversationState.SOLUTION_ANALYSIS:
            system_prompt = f"""You are providing a WiFi troubleshooting solution based on:
            Auto-test results and user answers: {symptoms.dict()}
            
            Explain your reasoning clearly and provide the recommended solution."""
            
        else:
            system_prompt = "You are a helpful WiFi troubleshooting assistant."

        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                max_tokens=250,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"I'm having trouble connecting right now. Let me help you manually."

    def parse_user_response(self, user_input: str, question_type: str, attribute: str, symptoms: UserSymptoms):
        """Parse and store user responses to qualifying questions"""
        user_input_lower = user_input.lower().strip()
        
        if question_type == "yes_no":
            if any(word in user_input_lower for word in ["yes", "yeah", "yep", "sure", "correct"]):
                setattr(symptoms, attribute, True)
            elif any(word in user_input_lower for word in ["no", "nope", "not", "can't", "cannot"]):
                setattr(symptoms, attribute, False)
        
        elif question_type == "number_or_unknown" or question_type == "number_or_text":
            if "unknown" in user_input_lower or "don't know" in user_input_lower:
                setattr(symptoms, attribute, None)
            else:
                try:
                    days = int(''.join(filter(str.isdigit, user_input)))
                    setattr(symptoms, attribute, days)
                except:
                    setattr(symptoms, attribute, None)
        
        elif question_type == "text":
            setattr(symptoms, attribute, user_input)
        
        elif question_type == "yes_no_text":
            if any(word in user_input_lower for word in ["yes", "yeah", "getting"]):
                setattr(symptoms, attribute, True)
            else:
                setattr(symptoms, attribute, False)
        
        elif question_type == "down_or_slow":
            if any(word in user_input_lower for word in ["completely", "down", "nothing", "no internet"]):
                symptoms.internet_completely_down = True
                symptoms.slow_speeds = False
            else:
                symptoms.internet_completely_down = False
                symptoms.slow_speeds = True

    def get_reboot_instructions(self) -> str:
        return """Perfect! Based on my analysis, a router reboot should resolve your WiFi issues. Here's how to do it safely:

**Step-by-step router reboot:**

1. **Unplug the power cable** from your router (and modem if separate)
2. **Wait 30 seconds** - this clears the memory completely
3. **Plug the modem back in first** (if you have a separate modem)
4. **Wait 1-2 minutes** for the modem to fully boot up
5. **Plug the router back in** and wait another 2-3 minutes
6. **Check if the WiFi network appears** on your device

This process usually takes about 5 minutes total. Let me know when you've completed these steps!"""

    def format_test_results(self, auto_results: AutoTestResults) -> str:
        """Format auto-test results for user display"""
        result_text = "🔍 **Connection Test Results:**\n\n"
        
        if auto_results.connectivity_status:
            result_text += "✅ **Internet Connection:** Connected\n"
        else:
            result_text += "❌ **Internet Connection:** Not Connected\n"
        
        if auto_results.speed_mbps:
            if auto_results.speed_mbps < 1:
                result_text += f" **Speed:** {auto_results.speed_mbps:.1f} Mbps (Very Slow)\n"
            elif auto_results.speed_mbps < 5:
                result_text += f" **Speed:** {auto_results.speed_mbps:.1f} Mbps (Slow)\n"
            else:
                result_text += f" **Speed:** {auto_results.speed_mbps:.1f} Mbps (Good)\n"
        
        if auto_results.latency_ms:
            if auto_results.latency_ms > 500:
                result_text += f"⏱️ **Response Time:** {auto_results.latency_ms}ms (High)\n"
            else:
                result_text += f"⏱️ **Response Time:** {auto_results.latency_ms}ms (Normal)\n"
        
        result_text += "\nNow let me ask you some targeted questions to get the complete picture..."
        
        return result_text
