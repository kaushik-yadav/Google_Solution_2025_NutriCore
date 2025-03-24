import os
import google.generativeai as genai
from PIL import Image
from datetime import datetime
from dotenv import load_dotenv
from database import Database


class CalorieEstimator:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Please set GOOGLE_API_KEY in your .env file")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-pro")

        self.vision_model = genai.GenerativeModel("gemini-1.5-flash")
        self.db = Database()

    def estimate_from_image(self, image_path):
        """Estimate calories from an image input"""
        try:
            image = Image.open(image_path)
            prompt = """Analyze the food in this image and provide the following details in one line using this exact format: "
                "Food: [name], Portion: [portion], Calories: [number] kcal, Protein: [number] g, Carbs: [number] g, Fat: [number] g. "
                "Do not include any extra text."""

            response = self.vision_model.generate_content([prompt, image])
            return self._parse_response(response.text)
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            return None

    def estimate_from_text(self, text_input):
        """Estimate calories from text input"""
        prompt = f"""Given this food description: "{text_input}"
        Please provide the following using name of food item + portion size:
        1. Estimated Protein in it.
        2. Estimated Fat in it
        3. Estimated Carbohydates in it
        4. Estimated calories.
        Give output in this format : 
        food: [name], portion: [portion], calories: [number] kcal, protein: [number] g, carbohydrates: [number] g, fat: [number] g. 
        Give no extra text"""

        response = self.model.generate_content(prompt)
        return self._parse_response(response.text)

    def _parse_response(self, response_text):
        """Parse the AI response into structured data"""
        try:
            # Extract information from response
            food = response_text.split("food:")[1].split(",")[0].strip()
            portion = response_text.split("portion:")[1].split(",")[0].strip()
            calories = response_text.split("calories:")[1].strip()
            protein = response_text.split("protein:")[1].strip()
            carbohydrates = response_text.split("carbohydrates:")[1].strip()
            fat = response_text.split("fat:")[1].strip()

            return {
                "food": food,
                "portion": portion,
                "calories": calories,
                "protein": protein,
                "carbohydrates": carbohydrates,
                "fat": fat,
            }
        except Exception as e:
            print(f"Error parsing response: {str(e)}")
            return None

    def log_calories(self, food_data, user_id):
        """Log calories to database"""
        if food_data:
            self.db.add_calorie_entry(
                user_id=user_id,
                food_name=food_data["food"],
                portion=food_data["portion"],
                calories=food_data["calories"],
                timestamp=datetime.now(),
            )
            return True
        return False

    def get_daily_summary(self, user_id):
        """Get daily calorie summary"""
        today = datetime.now().date()
        entries = self.db.get_calories_for_date(user_id, today)

        total_calories = sum(entry.calories for entry in entries)
        return {"total_calories": total_calories, "entries": entries}
