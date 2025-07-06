from typing import Tuple
from sklearn.metrics.pairwise import cosine_similarity
import json
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import os
from google import genai
from nats.aio.client import Client as NATS
from src.services.chroma_service import ChromaService
import logging

from src.services.variant_service import VariantService
from src.services.order_service import order_service

logger = logging.getLogger(__name__)

nc = NATS()

RETURN_POLICY = {
    "return_policy": "You can return any product within 30 days of purchase for a full refund. The product must be in its original condition and packaging."
}

PAYMENT_METHODS = {
    "payment_methods": [
        "QR Payment",
        "Cash on Delivery"
    ]
}

SHIPPING_METHODS = {
    "shipping_methods": {
        "Standard Shipping": "Delivery within 3-5 business days",
        "Same-Day Delivery": "Delivery within the same day"
    }
}


class FunctionCallingManager:
    def __init__(self):
        self.function_calls = []
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_file_path = "src/core/intent_embeddings.json"
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.chroma_service = ChromaService()
        self.variant_service = VariantService()
        # self.nats = NATS()
        # self.nats.max_payload_size = 1048576  # 1MB limit
        # self.pending_requests = {}

    def create_embedding(self, text: str, retry_count=3, delay=1) -> List[float]:
        embedding = self.model.encode(text, show_progress_bar=True)

        return embedding.tolist()

    def function_to_object(self, function_name: str) -> Dict[str, Any]:
        
        return {
            "name": function_name 
        }

    def load_json_embedding_file(self) -> List[Dict[str, Any]]:
        with open(self.embedding_file_path, 'r') as f:
            return json.load(f)

    def classify_intent_knn_and_cos(self, query: str, k: int = 3) -> Tuple[str, float]:
        # Tạo embedding cho câu truy vấn
        query_embedding = self.create_embedding(query)

        intent_embeddings = self.load_json_embedding_file()

        # Chuẩn bị danh sách để lưu trữ tất cả các độ tương đồng
        all_similarities = []

        # Tính độ tương đồng với tất cả các câu mẫu
        for item in intent_embeddings:  # Iterate through the list
            intent = item["tag"]
            example_embedding = np.array(item["embedding"])  # Convert to NumPy array

            similarity = cosine_similarity([query_embedding], [example_embedding])[0][0]
            all_similarities.append({
                "intent": intent,
                "similarity": similarity
            })

        # Sắp xếp theo độ tương đồng giảm dần
        all_similarities.sort(key=lambda x: x["similarity"], reverse=True)

        # Lấy k láng giềng gần nhất
        top_k = all_similarities[:k]

        # Đếm số lần xuất hiện của mỗi intent trong top k
        intent_counts = {}
        for item in top_k:
            intent = item["intent"]
            if intent in intent_counts:
                intent_counts[intent] += 1
            else:
                intent_counts[intent] = 1

        # Tìm intent phổ biến nhất
        if not intent_counts:
            return "unknown", 0.0  # Handle the case where no intents are found

        best_intent = max(intent_counts, key=intent_counts.get)

        # Tính độ tin cậy dựa trên số lần xuất hiện và độ tương đồng trung bình
        confidence = intent_counts[best_intent] / k
        avg_similarity = sum(item["similarity"] for item in top_k if item["intent"] == best_intent) / intent_counts[best_intent]

        # Kết hợp hai yếu tố để có độ tin cậy tổng thể
        overall_confidence = (confidence + avg_similarity) / 2

        if overall_confidence < 0.5:
            return "unknown"
        # Trả về intent tốt nhất và độ tin cậy
        best_intent = best_intent if overall_confidence >= 0.5 else "unknown"

        return best_intent
    
    def extract_parameters(self, query: str, function_name) -> Dict[str, Any]:
        """Trích xuất các tham số từ câu truy vấn."""
        # Define the function parameters based on function name
        function_params = {
            "greeting": [],
            "product_search": ["query"],
            "product_information_inquiry": ["product_name"],
            "product_dimensions": ["product_name"],
            "product_material": ["product_name"],
            "product_color": ["product_name"],
            "interior_design_advice": ["room_type", "style", "constraint", "goal"],
            "color_matching_advice": ["base_elements", "style", "atmosphere"],
            "price_inquiry": ["product_name"],
            "discount_inquiry": ["name", "code", "description", "start_date", "end_date", "is_active", "customer_level", "discount_percentage"],
            "order_status": ["status", "total_price", "discount", "final_price", "order_date", "shipping_address", "order_details"],
            "return_policy": [],
            "shipping_inquiry": ["order_id"],
            "payment_methods": [],
            "product_availability": ["product_name"],
            "thank_you": [],
            "goodbye": []
        }

        required_params = function_params.get(function_name, [])

        if not required_params:
            # If no parameters are required, return an empty dict
            return {}
        
        # Create a more specific prompt based on the required parameters
        param_desc = ", ".join([f"'{param}'" for param in required_params]) if required_params else "no parameters"
        prompt = f"""Extract parameters for the function '{function_name}' from this query: "{query}"

Required parameters: {param_desc}

Instructions:
1. Only extract the required parameters listed above
2. Return a simple JSON object with parameter names and values
3. If a parameter is not found, use a reasonable default or empty string

Example format:
{{
    {', '.join([f'"{param}": "<extracted value>"' for param in required_params]) if required_params else '"no_params": true'}
}}

Return only valid JSON, no additional text."""

        response = self.client.models.generate_content(
            contents=prompt,
            model="gemini-2.0-flash",
        )

        try:
            # Extract JSON from the response text
            text = response.text
            # Find the first { and last } to extract just the JSON part
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
                parameters = json.loads(json_str)
                return parameters
            return {}
        except (json.JSONDecodeError, AttributeError):
            # Return empty dict with required params if parsing fails
            return {param: "" for param in required_params} if required_params else {}

    async def call_function(self, function_name: str, parameters: Dict[str, Any], user_id: str | None) -> Any:
        """Gọi hàm tương ứng với tên hàm và tham số."""
        if function_name == "unknown":
            self.unknown_function = "Sorry, I couldn't understand your request. Could you please rephrase it or ask something else?"
            return self.unknown_function

        function_map = {
            "greeting": self.greeting,
            "product_search": self.product_search,
            "product_information_inquiry": self.product_information_inquiry,
            "product_dimensions": self.product_dimensions,
            "product_material": self.product_material,
            "product_color": self.product_color, 
            "interior_design_advice": self.interior_design_advice,
            "color_matching_advice": self.color_matching_advice,
            "price_inquiry": self.price_inquiry,
            "discount_inquiry": self.discount_inquiry,
            "order_status": self.order_status,
            "return_policy": self.return_policy,
            "shipping_inquiry": self.shipping_inquiry,
            "payment_methods": self.payment_methods,
            "product_availability": self.product_availability,
            "thank_you": self.thank_you,
            "goodbye": self.goodbye
        }

        if function_name == "order_status":
            parameters["user_id"] = user_id

        if function_name in function_map:
            return await function_map[function_name](**parameters)
        else:
            raise ValueError(f"Unknown function: {function_name}")

    async def greeting(self) -> str:
        """Hàm chào hỏi."""
        return json.dumps({"message": "Hello! How can I assist you today?"}, indent=2)
    
    async def product_search(self, query: str) -> str:
        """Hàm tìm kiếm sản phẩm."""
        # Giả sử bạn có một hàm tìm kiếm sản phẩm
        # Có thể sử dụng ChromaDB hoặc một dịch vụ tìm kiếm khác
        search_results = await self.variant_service.search_variants(
            query=query,
            limit=5,
        )
        if not search_results:
            return json.dumps({"error": "No products found matching your query."}, indent=2)    
        
        return json.dumps(search_results, indent=2)

    async def product_information_inquiry(self, product_name: str) -> str:
        """Hàm tra cứu thông tin sản phẩm."""
        search_results = await self.variant_service.search_variants(
            query=product_name,
            limit=1
        )
        if not search_results:
            return json.dumps({"error": "No information found for the specified product."}, indent=2)
        
        return json.dumps(search_results, indent=2)  
    
    async def product_dimensions(self, product_name: str) -> str:
        """Hàm tra cứu kích thước sản phẩm."""
        search_results = await self.variant_service.search_variants(
            query=product_name,
            limit=1
        )
        if not search_results:
            return json.dumps({"error": "No dimensions found for the specified product."}, indent=2)
        
        # Convert search results to JSON format
        product_info = search_results[0].get('metadata', {})
        dimensions = product_info.get('dimensions', 'Dimensions not available')
        return json.dumps({"product_name": product_name, "dimensions": dimensions}, indent=2)
    
    async def product_material(self, product_name: str) -> str:
        """Hàm tra cứu chất liệu sản phẩm."""
        search_results = await self.variant_service.search_variants(
            query=product_name,
            limit=1
        )
        if not search_results:
            return json.dumps({"error": "No material information found for the specified product."}, indent=2)
        
        # Convert search results to JSON format
        product_info = search_results[0].get('metadata', {})
        material = product_info.get('material', 'Material not available')
        return json.dumps({"product_name": product_name, "material": material}, indent=2)
    
    async def product_color(self, product_name: str) -> str:
        """Hàm tra cứu màu sắc sản phẩm."""
        search_results = await self.variant_service.search_variants(
            query=product_name,
            limit=1
        )
        if not search_results:
            return json.dumps({"error": "No color information found for the specified product."}, indent=2)
        
        # Convert search results to JSON format
        product_info = search_results[0].get('metadata', {})
        color = product_info.get('color', 'Color not available')
        return json.dumps({"product_name": product_name, "color": color}, indent=2)

    async def interior_design_advice(self, room_type: str, style: str, constraint: str, goal: str) -> str:
        """Hàm tư vấn thiết kế nội thất."""
        # Giả sử bạn có một hàm tư vấn thiết kế nội thất
        return json.dumps({
            "advice": f"Providing interior design advice for {room_type} in {style} style with constraints: {constraint} and goal: {goal}"
        }, indent=2)

    async def color_matching_advice(self, base_elements: List[str], style: str, atmosphere: str) -> str:
        """Hàm tư vấn phối màu."""
        # Giả sử bạn có một hàm tư vấn phối màu
        return json.dumps({"advice": f"Providing color matching advice for: {base_elements} in {style} style with atmosphere: {atmosphere}"}, indent=2)

    async def price_inquiry(self, product_name: str) -> str:
        search_results = await self.variant_service.search_variants(product_name, n_results=1)
        """Hàm tra cứu giá sản phẩm."""
        if not search_results:
            return json.dumps({"error": "No price information found for the specified product."}, indent=2)
        # Convert search results to JSON format
        product_info = search_results[0].get('metadata', {})
        price = product_info.get('price', 'Price not available')
        return json.dumps({"product_name": product_name, "price": price}, indent=2)

    async def discount_inquiry(self, name: str = "", code: str = "", description: str = "", customer_level: str = "", is_active: bool = True, start_date: str = "", end_date: str = "", discount_percentage: float = 0.0) -> str:
        from src.services.promotion_service import PromotionService
        """Hàm tra cứu thông tin khuyến mãi."""
        promotion_service = PromotionService()
        # Build the search query from all provided parameters
        query = " ".join(filter(None, [
            name,
            code,
            description,
            customer_level,
            str(is_active) if isinstance(is_active, bool) else is_active,
            start_date,
            end_date, 
            str(discount_percentage) if discount_percentage else ""
        ]))

        promotions = await promotion_service.search_promotions(query=query, n_results=5)
        if not promotions:
            return json.dumps({"error": "No promotions found."}, indent=2)
        return json.dumps(promotions, indent=2)

    async def order_status(self, user_id: str = "", status: str = "", total_price: float = 0.0, discount: float = 0.0, final_price: float = 0.0, order_date: str = "", shipping_address: str = "", order_details: list = None) -> str:
        query = " ".join(filter(None, [
            status,
            str(total_price) if total_price else "",
            str(discount) if discount else "",
            str(final_price) if final_price else "",
            order_date,
            shipping_address,
            " ".join(order_details) if order_details else ""
        ]))

        orders = await order_service.search_orders(query=query, user_id=user_id, limit=5)
        if not orders:
            return json.dumps({"error": "No orders found."}, indent=2)

        # Convert orders to JSON format
        return json.dumps(orders, indent=2)

    async def return_policy(self) -> str:
        """Hàm tra cứu chính sách đổi trả."""
        # Giả sử bạn có một hàm tra cứu chính sách đổi trả
        return json.dumps(RETURN_POLICY, indent=2)

    async def shipping_inquiry(self, order_id: str) -> str:
        """Hàm tra cứu thông tin vận chuyển."""
        # Giả sử bạn có một hàm tra cứu thông tin vận chuyển
        return f"Checking shipping details for order ID: {order_id}"

    async def payment_methods(self) -> str:
        """Hàm tra cứu phương thức thanh toán."""
        # Giả sử bạn có một hàm tra cứu phương thức thanh toán
        return json.dumps(PAYMENT_METHODS, indent=2)

    async def product_availability(self, product_name: str) -> str:
        """Hàm kiểm tra tình trạng sản phẩm."""
        # Giả sử bạn có một hàm kiểm tra tình trạng sản phẩm
        search_results = await self.chroma_service.search_variants(product_name, n_results=1)
        if not search_results:
            return json.dumps({"product_name": product_name, "availability": search_results.get('is_active', False)}, indent=2)
        # Convert search results to JSON format
        product_info = search_results[0].get('metadata', {})
        availability = product_info.get('is_active', 'Availability not specified')
        return json.dumps({"product_name": product_name, "availability": availability}, indent=2)

    async def thank_you(self) -> str:
        """Hàm cảm ơn."""
        return json.dumps({"message": "Thank you for your inquiry! If you have any more questions, feel free to ask."}, indent=2)

    async def goodbye(self) -> str:
        """Hàm chào tạm biệt."""
        return json.dumps({"message": "Goodbye! Have a great day!"}, indent=2)
