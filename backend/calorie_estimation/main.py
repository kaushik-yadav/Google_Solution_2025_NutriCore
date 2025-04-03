from calorie_estimator import CalorieEstimator
from database import Database
import os
import requests


def main():
    # Initialize the system
    estimator = CalorieEstimator()
    db = Database()

    # Create a test user
    user_id = db.add_user("test_user", daily_calorie_goal=2000)
    print(f"Created user with ID: {user_id}")

    while True:
        print("\n=== Calorie Estimation System ===")
        print("1. Estimate calories from text")
        print("2. Estimate calories from image (Upload)")
        print("3. View today's summary")
        print("4. Exit")

        choice = input("\nEnter your choice (1-4): ")

        if choice == "1":
            food_desc = input("Enter food description (e.g., '2 cups of rice'): ")
            result = estimator.estimate_from_text(food_desc)
            if result:
                print("\nEstimated Nutritional Values:")
                for key, value in result.items():
                    print(f"- {key.capitalize()}: {value}")
                estimator.log_calories(result, user_id)
            else:
                print("Failed to estimate calories. Please try again.")

        elif choice == "2":
            print("Please upload an image file (JPEG, PNG, etc.)")
            file_name = input(
                "Enter the image file name (ensure it's in the same directory): "
            )

            if not os.path.isfile(file_name):
                print("File not found. Ensure the file exists and try again.")
                continue
            print(file_name)
            food_item = estimator.analyze_food_image(file_name)
            print("this is the itentified food item :", food_item)
            if food_item:
                print(f"Detected food: {food_item}")
                serving_size = input(
                    f"Enter serving size for {food_item} (e.g., '1 plate', '200 grams'): "
                )
                query = f"{serving_size} of {food_item}"
                result = estimator.estimate_from_text(query)
                if result:
                    print("\nEstimated Nutritional Values:")
                    for key, value in result.items():
                        print(f"- {key.capitalize()}: {value}")
                    estimator.log_calories(result, user_id)
                else:
                    print("Failed to estimate calories.")
            else:
                print(
                    "Could not recognize the food item. Try again with a clearer image."
                )

        elif choice == "3":
            summary = estimator.get_daily_summary(user_id)
            print("\n=== Today's Summary ===")
            print(f"Total calories: {summary['total_calories']}")
            print("\nFood entries:")
            for entry in summary["entries"]:
                print(
                    f"- {entry.food_name}: {entry.calories} calories ({entry.portion})"
                )

        elif choice == "4":
            print("Goodbye!")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
