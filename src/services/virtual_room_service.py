from typing import Dict, List, Optional, Any, TypedDict, Union
import uuid
import json
import os
from datetime import datetime
import decimal
import re
from google import genai
from google.genai import types

# Type definitions
class FurniturePlacement(TypedDict):
    furniture_id: str
    name: str
    category: str
    dimensions: Dict[str, float]
    color: str
    position: Dict[str, float]
    rotation: Dict[str, float]
    explanation: str

class LayoutResponse(TypedDict):
    layout: Dict[str, Union[str, List[FurniturePlacement], List[Dict[str, str]]]]

# Constants
SYSTEM_INSTRUCTION = """
You are Roomie, an expert interior design AI assistant for DearHome.

Your task is to create a detailed room layout based on the provided room dimensions, furniture items, and user preferences.

IMPORTANT: Your response MUST be in valid JSON format with the following structure:
{
  "layout": {
    "room_id": "unique_identifier",
    "design_name": "Name of the design",
    "furniture_placement": [
      {
        "furniture_id": "id of the furniture item",
        "name": "name of the furniture",
        "modelUrl": "URL to the 3D model of the furniture",
        "category": "category of the furniture",
        "dimensions": {"width": float, "length": float, "height": float},
        "color": "color of the furniture",
        "position": {"x": float, "y": float, "z": float},
        "rotation": {"y": float},
        "explanation": "why this item is placed here"
      }
    ],
    "design_explanation": "overall explanation of the design",
    "style_description": "description of the design style",
    "additional_recommendations": [
      {
        "category": "product category",
        "description": "recommendation description"
      }
    ]
  }
}

Follow these guidelines:
1. Position coordinates should be within the room dimensions
2. Furniture should not overlap with doors, windows, or other furniture
3. Create a functional and aesthetically pleasing arrangement
4. Consider traffic flow and accessibility
5. Align furniture with the user's style preferences
6. Provide thoughtful explanations for each placement decision
7. Suggest 2-3 additional items that would complement the design

DO NOT include any text outside of this JSON structure. Ensure the JSON is valid and properly formatted.
"""

class VirtualRoomService:
    def __init__(self):
        """Initialize the VirtualRoomService with Gemini AI configuration."""
        self.config = {
            "automatic_function_calling": {"disable": True},
            "tool_config": {"function_calling_config": {"mode": "any"}},
        }
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.chat = self.client.chats.create(
            model="gemini-2.0-flash",
            config=self.config,
        )

    @staticmethod
    def _serialize_json(obj: Any) -> Any:
        """Convert special types to JSON-serializable formats."""
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    @staticmethod
    def _convert_uuids(obj: Any) -> Any:
        """Recursively convert UUIDs to strings in nested structures."""
        if isinstance(obj, dict):
            return {k: VirtualRoomService._convert_uuids(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [VirtualRoomService._convert_uuids(item) for item in obj]
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        return obj

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate AI response text into JSON format."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            return {
                "error": True,
                "message": "Failed to parse AI response as JSON",
                "raw_response": response
            }

    async def get_variants_with_details(self, variant_ids: List[uuid.UUID]) -> Dict[str, Any]:
        """
        Fetch variant details from the database and convert UUIDs to strings.
        
        Args:
            variant_ids: List of UUID objects representing variant IDs
            
        Returns:
            Dictionary containing success status and variant details
        """
        variant_queries = VariantQueries()
        str_variant_ids = [str(vid) for vid in variant_ids]
        variants_details = variant_queries.get_variants_with_details(ids=str_variant_ids)

        if not variants_details.get("success"):
            return {"error": variants_details.get("error", "Failed to fetch variant details")}

        variants = variants_details.get("result", [])
        converted_variants = self._convert_uuids(variants)

        return {
            "success": True,
            "variants": converted_variants
        }

    async def _create_detailed_prompt(
        self,
        room_info: Dict[str, Any],
        furniture_ids: List[uuid.UUID],
        prompt: str,
        options: Dict[str, Any]
    ) -> str:
        """
        Create a detailed prompt for the AI based on room info, furniture, and user preferences.
        
        Args:
            room_info: Dictionary containing room details
            furniture_ids: List of furniture UUIDs
            prompt: User's original prompt
            options: Dictionary of design options
            
        Returns:
            Formatted prompt string for the AI
        """
        # Format room information
        room_desc = f"""
Room Information:
```json
{json.dumps(room_info, indent=2)}
```
- Type: {room_info.get('room_type', 'living room')}
- Dimensions: {room_info.get('width', 0)}m width × {room_info.get('length', 0)}m length × {room_info.get('height', 0)}m height
- Wall Color: {room_info.get('wall_color', 'white')}
- Floor Type: {room_info.get('floor_type', 'wooden')}
"""

        # Format windows and doors information
        windows_desc = self._format_windows_desc(room_info.get('windows', []))
        doors_desc = self._format_doors_desc(room_info.get('doors', []))

        # Get and format furniture details
        furniture_details = await self.get_variants_with_details(furniture_ids)
        if not furniture_details.get("success"):
            return {"error": furniture_details.get("error", "Failed to fetch furniture details")}
        
        furniture_desc = self._format_furniture_desc(furniture_details.get("variants", []))
        options_desc = self._format_options_desc(options)

        return f"{room_desc}\n{windows_desc}\n{doors_desc}\n{furniture_desc}\n{options_desc}\nUser Prompt: {prompt}"

    @staticmethod
    def _format_windows_desc(windows: List[Dict[str, Any]]) -> str:
        """Format windows information into a readable string."""
        desc = "Windows:\n"
        for i, window in enumerate(windows, 1):
            pos = window.get('position', {})
            desc += (
                f"- Window {i}: Position (x={pos.get('x', 0)}, y={pos.get('y', 0)}, z={pos.get('z', 0)}), "
                f"Size: {window.get('width', 0)}m × {window.get('height', 0)}m\n"
            )
        return desc

    @staticmethod
    def _format_doors_desc(doors: List[Dict[str, Any]]) -> str:
        """Format doors information into a readable string."""
        desc = "Doors:\n"
        for i, door in enumerate(doors, 1):
            pos = door.get('position', {})
            desc += (
                f"- Door {i}: Position (x={pos.get('x', 0)}, y={pos.get('y', 0)}, z={pos.get('z', 0)}), "
                f"Size: {door.get('width', 0)}m × {door.get('height', 0)}m\n"
            )
        return desc

    def _format_furniture_desc(self, variants: List[Dict[str, Any]]) -> str:
        """Format furniture information into a readable string."""
        desc = "Furniture Items:\n"
        for i, furniture in enumerate(variants, 1):
            desc += f"- Furniture {i}:\n```json\n{json.dumps(furniture, indent=2, default=self._serialize_json)}\n```\n"
        return desc

    @staticmethod
    def _format_options_desc(options: Dict[str, Any]) -> str:
        """Format design options into a readable string."""
        return (
            "Design Options:\n"
            f"- Number of Designs: {options.get('number_of_designs', 1)}\n"
            f"- Style Preference: {options.get('style_preference', 'modern')}\n"
            f"- Priority: {options.get('priority', 'balance')}\n"
        )

    async def get_virtual_room_layout(
        self,
        room_info: Dict[str, Any],
        furniture_ids: List[uuid.UUID],
        prompt: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a virtual room layout based on provided information.
        
        Args:
            room_info: Dictionary containing room details
            furniture_ids: List of furniture UUIDs
            prompt: User's design prompt
            options: Dictionary of design options
            
        Returns:
            Dictionary containing the generated layout or error information
        """
        detailed_prompt = await self._create_detailed_prompt(room_info, furniture_ids, prompt, options)

        contents = [
            types.Content(
                role="model",
                parts=[types.Part(text=SYSTEM_INSTRUCTION)]
            ),
            types.Content(
                role="user",
                parts=[types.Part(text=detailed_prompt)]
            ),
        ]

        generation_config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.2,
            top_p=0.8,
            top_k=40,
            max_output_tokens=2048,
        )

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
                config=generation_config,
            )
            return self._parse_ai_response(response.text)
            
        except Exception as e:
            return {
                "error": True,
                "message": f"Error generating room layout: {str(e)}",
            }




