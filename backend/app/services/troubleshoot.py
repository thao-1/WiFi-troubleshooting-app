import openai
from typing import List, Dict, Optional, Tuple, Any
from app.models.schemas import (
    ConversationState, UserSymptoms, ChatMessage, SessionData, AutoTestResults
)
from app.core.config import settings

openai.api_key = settings.openai_api_key

class WiFiTroubleshootService:
    def __init__(self):
        # Different question sets based on auto-test results
        self.question_sets = {
            "no_connectivity": [
                {
                    "question": "Can you see your WiFi network name in the list of available networks on your device?",
                    "attribute": "can_see_network",
                    "type": "yes_no"
                },
                {
                    "question": "What color are the lights on your router right now? (Green, Red, Orange, Blinking, etc.)",
                    "attribute": "router_lights_status", 
                    "type": "text"
                },
                {
                    "question": "Are other devices in your home (other phones, laptops, smart TVs) also unable to connect?",
                    "attribute": "multiple_devices_affected",
                    "type": "yes_no"
                },
                {
                    "question": "When was the last time you unplugged and restarted your router?",
                    "attribute": "days_since_last_reboot",
                    "type": "number_or_text"
                },
                {
                    "question": "Are you getting any specific error messages when trying to connect? If yes, what do they say?",
                    "attribute": "error_messages_seen",
                    "type": "yes_no_text"
                }
            ],
            "slow_speed": [
                {
                    "question": "Are other devices in your home also experiencing slow internet speeds?",
                    "attribute": "multiple_devices_affected",
                    "type": "yes_no"
                },
                {
                    "question": "Is the slowness affecting all websites and apps, or just specific ones?",
                    "attribute": "specific_websites_affected",
                    "type": "all_or_specific"
                },
                {
                    "question": "How many days has it been since you last restarted your router by unplugging it?",
                    "attribute": "days_since_last_reboot",
                    "type": "number_or_text"
                },
                {
                    "question": "Do you notice the slowness more at certain times of day, or is it constant?",
                    "attribute": "intermittent_connection",
                    "type": "constant_or_intermittent"
                },
                {
                    "question": "Are you able to connect to your WiFi network normally, or do you also have trouble connecting?",
                    "attribute": "can_connect",
                    "type": "yes_no"
                }
            ],
            "intermittent": [
                {
                    "question": "Does your WiFi disconnect and reconnect on its own, or do you have to manually reconnect?",
                    "attribute": "intermittent_connection",
                    "type": "automatic_or_manual"
                },
                {
                    "question": "Are other devices in your home also experiencing these disconnections?",
                    "attribute": "multiple_devices_affected",
                    "type": "yes_no"
                },
                {
                    "question": "Can you still see your WiFi network name when it disconnects, or does it disappear completely?",
                    "attribute": "can_see_network",
                    "type": "visible_or_disappears"
                },
                {
                    "question": "How long has it been since you last restarted your router?",
                    "attribute": "days_since_last_reboot",
                    "type": "number_or_text"
                },
                {
                    "question": "Do the disconnections happen more during certain activities (streaming, video calls, etc.)?",
                    "attribute": "specific_websites_affected",
                    "type": "activity_specific"
                }
            ],
            "default": [
                {
                    "question": "Can you see your WiFi network name when you look for available networks on your device?",
                    "attribute": "can_see_network",
                    "type": "yes_no"
                },
                {
                    "question": "Are you able to connect to the WiFi network, or does it fail when you try?",
                    "attribute": "can_connect",
                    "type": "yes_no"
                },
                {
                    "question": "Are other devices in your home (phones, laptops, tablets) having the same WiFi problems?",
                    "attribute": "multiple_devices_affected",
                    "type": "yes_no"
                },
                {
                    "question": "How many days has it been since you last restarted/rebooted your router? (Enter a number, or 'unknown' if you're not sure)",
                    "attribute": "days_since_last_reboot",
                    "type": "number_or_unknown"
                },
                {
                    "question": "Is your internet completely down, or are you getting slow/intermittent connections?",
                    "attribute": "internet_completely_down",
                    "type": "down_or_slow"
                }
            ]
        }

    def determine_question_path(self, auto_test_results: Optional[AutoTestResults]) -> str:
        """Determine which set of questions to ask based on auto-test results"""
        if not auto_test_results:
            return "default"
        
        if not auto_test_results.connectivity_status:
            return "no_connectivity"
        elif auto_test_results.speed_mbps and auto_test_results.speed_mbps < 2:
            return "slow_speed"
        elif auto_test_results.latency_ms and auto_test_results.latency_ms > 500:
            return "intermittent"
        else:
            return "default"

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
                result_text += f"🐌 **Speed:** {auto_results.speed_mbps:.1f} Mbps (Very Slow)\n"
            elif auto_results.speed_mbps < 5:
                result_text += f"🚶 **Speed:** {auto_results.speed_mbps:.1f} Mbps (Slow)\n"
            else:
                result_text += f"🚀 **Speed:** {auto_results.speed_mbps:.1f} Mbps (Good)\n"
        
        if auto_results.latency_ms:
            if auto_results.latency_ms > 500:
                result_text += f"⏱️ **Response Time:** {auto_results.latency_ms}ms (High)\n"
            else:
                result_text += f"⏱️ **Response Time:** {auto_results.latency_ms}ms (Normal)\n"
        
        result_text += "\nNow let me ask you some targeted questions to get the complete picture..."
        
        return result_text