from calorie_estimator import CalorieEstimator
from database import Database


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
        print("2. Estimate calories from image")
        print("3. View today's summary")
        print("4. Exit")

        choice = input("\nEnter your choice (1-4): ")

        if choice == "1":
            # Text-based estimation
            food_desc = input("Enter food description (e.g., '2 cups of rice'): ")
            result = estimator.estimate_from_text(food_desc)
            if result:
                print(f"\nEstimated Nutritional Values:")
                print(f"- Calories: {result['calories']} kcal")
                print(f"- Protein: {result['protein']} g")
                print(f"- Carbs: {result['carbohydrates']} g")
                print(f"- Fat: {result['fat']} g")
                estimator.log_calories(result, user_id)
            else:
                print("Failed to estimate calories. Please try again.")

        elif choice == "2":
            # Image-based estimation with error handling
            image_path = input("Enter the path to your food image: ")
            try:
                result = estimator.estimate_from_image(image_path)
                if result:
                    print(f"\nEstimated Nutritional Values:")
                    print(f"- Calories: {result['calories']} kcal")
                    print(f"- Protein: {result['protein']} g")
                    print(f"- Carbs: {result['carbohydrates']} g")
                    print(f"- Fat: {result['fat']} g")
                    estimator.log_calories(result, user_id)
                else:
                    raise ValueError("Failed to process image.")
            except Exception as e:
                print(f"Error processing image: {e}")
                print(
                    "Image-based estimation failed. Please enter the food details manually."
                )

                # Ask user for text input instead
                food_desc = input("Enter food description (e.g., '2 cups of rice'): ")
                result = estimator.estimate_from_text(food_desc)
                if result:
                    print(f"\nEstimated calories: {result['calories']}")
                    print(f"Food: {result['food']}")
                    print(f"Portion: {result['portion']}")
                    estimator.log_calories(result, user_id)
                else:
                    print(
                        "Failed to estimate calories from text as well. Please try again."
                    )

        elif choice == "3":
            # View daily summary
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
