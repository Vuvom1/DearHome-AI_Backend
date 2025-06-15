from src.querries.user_querries import UserQueries

class UserService:
    def __init__(self):
        self.user_queries = UserQueries()

    def get_user_information(self, username):
        result = self.user_queries.get_user_by_username(username)
        
        if not result.get("success"):
            return {"error": result.get("error", "User not found")}
        
        user_data = result.get("result", {})
        
        # Return simplified user data
        formatted_user = {
            "id": user_data.get("Id"),
            "username": user_data.get("UserName"),
            "email": user_data.get("Email"),
            "phone_number": user_data.get("PhoneNumber"),
            "name": f"{user_data.get('Name', '')}",
            "account_status": "Active" if not user_data.get("LockoutEnd") else "Locked"
        }
        
        # Return the formatted user data
        return formatted_user
