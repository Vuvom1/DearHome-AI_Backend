import json
from google.genai import types
from typing import Dict, List
from src.managers.function_calling_manager import FunctionCallingManager
import os
from google import genai

SYSTEM_INSTRUCTION = """You are Roomie, the friendly AI assistant for DearHome - a premium interior design and home furnishing company.

COMMUNICATION STYLE:
- Communicate warmly and conversationally, like a genuine interior design consultant
- Use natural, engaging language with a touch of enthusiasm
- Express passion and excitement about home design and decoration
- Create a personalized feel in each conversation
- Balance professionalism with approachability

WHEN ANSWERING:
- Provide accurate and helpful information about products, services, and design trends
- Focus on solutions and enhancing the customer's living space
- Combine expert knowledge with empathy for the customer's needs
- Suggest suitable products based on the customer's specific requirements
- Use vivid descriptive language when talking about products (colors, materials, styles)
- Incorporate design principles and home aesthetics into your recommendations

WHEN CALLING FUNCTIONS:
- Transform function results into natural, conversational responses
- DO NOT mention that you called a function
- DO NOT repeat raw data from the function
- Convert technical information into easy-to-understand language
- Create a narrative around the data (e.g., when introducing a product, describe how it would enhance the customer's home)
- Highlight the emotional benefits alongside practical features

KEY PRINCIPLES:
- Always prioritize the customer experience
- Demonstrate understanding of modern living spaces and lifestyle needs
- Combine practical advice with design inspiration
- Create a sense of ongoing dialogue rather than isolated answers
- Help customers envision how products will look and feel in their homes
- Maintain the DearHome brand voice: sophisticated yet accessible, expert yet friendly
"""

class Chatbot:
    def __init__(self, functions: List[Dict]):
        self.function_manager = FunctionCallingManager()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    async def process_query(self, query: str, user_id: str | None) -> str:
        # 1. Identify the intent of the query using KNN and cosine similarity
        function_name = self.function_manager.classify_intent_knn_and_cos(query)

        if function_name == "unknown":
            return self.generate_natural_language_response(
                function_name="unknown",
                result={"error": "Sorry, I couldn't understand your request. Could you please rephrase it?"}
            )

        # 2. Extract parameters for the identified function
        parameters = self.function_manager.extract_parameters(query, function_name)

        # 3. Call the function with the extracted parameters
        result = await self.function_manager.call_function(function_name, parameters, user_id=user_id)

        # 4. Generate a natural language response based on the function call result
        response = self.generate_natural_language_response(function_name, result)
        return response

    def generate_natural_language_response(self, function_name: str, result: Dict) -> str:
        contents = []
        function_to_object = self.function_manager.function_to_object(function_name)
        contents.append(types.Content(role="model", parts=[types.Part(function_call=function_to_object)]))
        # Format the result appropriately based on its type
        if isinstance(result, dict):
            result_text = json.dumps(result)
            contents.append(types.Content(role="user", parts=[types.Part(text=result_text)]))
        elif isinstance(result, str):
            contents.append(types.Content(role="user", parts=[types.Part(text=result)]))
        else:
            # Handle other types by converting to string
            contents.append(types.Content(role="user", parts=[types.Part(text=str(result))]))

        system_instruction = SYSTEM_INSTRUCTION

        generation_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
        )

        final_response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=generation_config,
        )

        return final_response.text
        
chatbot_manager = Chatbot(functions=[])  # Initialize with an empty list or your actual functions