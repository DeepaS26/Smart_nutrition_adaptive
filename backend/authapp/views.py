from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .serializers import UserSerializer,UserProfileSerializer,FullUserSerializer
import joblib
import pandas as pd
import numpy as np
from rest_framework import status
from .models import UserProfile
import random


User = get_user_model()

# Load Models
diabetes_model = joblib.load(r"authapp/data/diabetes_model (1).pkl")
cardio_model = joblib.load(r"authapp/data/cardio_model (1).pkl")

# Load Recipes Data
recipes_df = pd.read_csv(r"authapp/data/final_rexipe(in) (1) (2).csv")
recipes_df['Diet'] = recipes_df['Diet'].str.strip().str.lower()


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import pandas as pd

@api_view(['POST'])
def predict_diet(request):
    """Predict diet recommendations based on user profile."""
   
    data = request.data.copy()
    print(data)
    serializer = UserProfileSerializer(data=data)
    print("To serialir:\n ",data)
    if serializer.is_valid():
        user_profile = serializer.validated_data
        print("From serializers:\n",user_profile)
        # Handle missing values safely
        glucose = user_profile.get('daily_insulin_level', 0)
        weight = user_profile.get('weight', 0)
        height = user_profile.get('height', 1)  # Avoid division by zero
        bmi = weight / ((height / 100) ** 2)
        age = user_profile.get('age', 0)
        systolic_bp = user_profile.get('systolic_bp', 0)
        diastolic_bp = user_profile.get('diastolic_bp', 0)
        cholesterol = user_profile.get('cholesterol', 0)
        gender = 1 if(user_profile.get('gender', '').lower() == 'male'  or  user_profile.get('gender', '').lower() == 'female') else 0
        family_history = user_profile.get('family_history', '').lower()
        health_condition_preferences = user_profile.get('health_condition_preferences', '').lower()
        dietary_preferences = user_profile.get('dietary_preferences', '').lower()

        # Prepare input data for prediction
        input_data = pd.DataFrame([[glucose, bmi, systolic_bp, diastolic_bp, cholesterol, age, gender]],
                                  columns=['Glucose', 'BMI', 'Systolic_BP', 'Diastolic_BP', 'cholesterol', 'Age', 'gender'])

        try:
            predicted_outcome = diabetes_model.predict(input_data)[0]
            
            predicted_cardio = cardio_model.predict(input_data)[0]
        except Exception as e:
            return Response({"error": f"Model prediction error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Determine health conditions
        is_diabetic = (predicted_outcome == 1) or (family_history == 'diabetic') or (health_condition_preferences in ['diabetes', 'both'])
        has_cardio = (predicted_cardio == 1) or (health_condition_preferences in ['cardiovascular', 'both'])

        print("HE:",health_condition_preferences)
        print("Diet: ",dietary_preferences)
        print("diabetes:",is_diabetic)
        print("cardio:",has_cardio)
        
        # Adjust recipes for health conditions
        if is_diabetic:
            if dietary_preferences=='vegetarian':
                recommended_recipes = recipes_df[
                            (recipes_df["Diet"].str.lower().isin(["vegetarian","high protein vegetarian"])) &  # Vegetarian diet
                            (recipes_df['carb_g_x'] <= 50) |( # Low-carb
                            (recipes_df['fat_g_x'] <= 25) )& # Low-fa
                            (
                            (recipes_df['fibre_g_x'] >= 5) |  # High-fiber
                            (recipes_df['protein_g_x'] >= 15)  # High protein
                            )
                            ]
            elif dietary_preferences=='vegan':  # Vegan
                    recommended_recipes = recipes_df[
                         (recipes_df['Diet'].str.lower() == 'vegan') &  # Vegan diet
                         (recipes_df['carb_g_x'] <= 50) |( # Low-carb
                        (recipes_df['fat_g_x'] <= 25) )& # Low-fa
                        (
                        (recipes_df['fibre_g_x'] >= 5) |  # High-fiber
                        (recipes_df['protein_g_x'] >= 15)  # High protein
                        )
                        
                    ]
            else:  # Non-Vegetarian
              print("Hrllo")
              recommended_recipes = recipes_df[
                (recipes_df["Diet"].str.lower().isin(["non vegeterian", "high protein non vegetarian"])) &  # Non-vegetarian diet
                (recipes_df['carb_g_x'] <= 50) |( # Low-carb
                (recipes_df['fat_g_x'] <= 25) )& # Low-fa
                (
                (recipes_df['fibre_g_x'] >= 5) |  # High-fiber
                (recipes_df['protein_g_x'] >= 15)  # High protein
                )
                ]
    
   
            
        if is_diabetic==False:
            if dietary_preferences=='vegetarian':
                recommended_recipes = recipes_df[recipes_df["Diet"].str.lower().isin(["vegetarian","high protein vegetarian"])]
            elif dietary_preferences=='vegan':
                recommended_recipes = recipes_df[recipes_df['Diet'].str.lower()== 'vegan']
            elif dietary_preferences=='non vegetarian':
                print("here")
                print(recipes_df[recipes_df["Diet"].str.lower().isin(["non vegeterian"])])
                print("hey")
                recommended_recipes =recipes_df[np.logical_not(recipes_df["Diet"].str.lower().isin(["vegetarian",'vegan','high protein vegetarian']))]
                print("recc",recommended_recipes)

            else:
                 recommended_recipes = recipes_df[recipes_df['Diet'].str.lower().isin(['vegetarian', 'non vegetarian', 'vegan'])]

        
        if has_cardio:
            if dietary_preferences=='vegetarian':
                recommended_recipes = recipes_df[
                            (recipes_df["Diet"].str.lower().isin(["vegetarian","high protein vegetarian"])) &  # Vegetarian diet
                            (recipes_df['carb_g_x'] <= 50) |( # Low-carb
                            (recipes_df['fat_g_x'] <= 25) )& # Low-fa
                            (
                            (recipes_df['fibre_g_x'] >= 5) |  # High-fiber
                            (recipes_df['protein_g_x'] >= 15)  # High protein
                            )
                            ]
            elif dietary_preferences=='vegan':  # Vegan
                    recommended_recipes = recipes_df[
                         (recipes_df['Diet'].str.lower() == 'vegan') &  # Vegan diet
                         (recipes_df['carb_g_x'] <= 50) |( # Low-carb
                        (recipes_df['fat_g_x'] <= 25) )& # Low-fa
                        (
                        (recipes_df['fibre_g_x'] >= 5) |  # High-fiber
                        (recipes_df['protein_g_x'] >= 15)  # High protein
                        )
                        
                    ]
            else:  # Non-Vegetarian
              print("Hrllo")
              recommended_recipes = recipes_df[
                (recipes_df["Diet"].str.lower().isin(["non vegeterian", "high protein non vegetarian"])) &  # Non-vegetarian diet
                (recipes_df['carb_g_x'] <= 50) |( # Low-carb
                (recipes_df['fat_g_x'] <= 25) )& # Low-fa
                (
                (recipes_df['fibre_g_x'] >= 5) |  # High-fiber
                (recipes_df['protein_g_x'] >= 15)  # High protein
                )
                ]
        print(dietary_preferences)
        print(health_condition_preferences)

        if health_condition_preferences=='none':
            if dietary_preferences=='vegetarian':
                recommended_recipes = recipes_df[
                            (recipes_df["Diet"].str.lower().isin(["vegetarian","high protein vegetarian"])) &  # Vegetarian diet
                            (recipes_df['carb_g_x'] <= 50) |( # Low-carb
                            (recipes_df['fat_g_x'] <= 25) )& # Low-fa
                            (
                            (recipes_df['fibre_g_x'] >= 5) |  # High-fiber
                            (recipes_df['protein_g_x'] >= 15)  # High protein
                            )
                            ]
            elif dietary_preferences=='vegan':  # Vegan
                    recommended_recipes = recipes_df[
                         (recipes_df['Diet'].str.lower() == 'vegan') &  # Vegan diet
                         (recipes_df['carb_g_x'] <= 50) |( # Low-carb
                        (recipes_df['fat_g_x'] <= 25) )& # Low-fa
                        (
                        (recipes_df['fibre_g_x'] >= 5) |  # High-fiber
                        (recipes_df['protein_g_x'] >= 15)  # High protein
                        )
                        
                    ]
            else:  # Non-Vegetarian
              recommended_recipes = recipes_df[
                (recipes_df["Diet"].str.lower().isin(["non vegeterian", "high protein non vegetarian"])) &  # Non-vegetarian diet
                (recipes_df['carb_g_x'] <= 50) |( # Low-carb
                (recipes_df['fat_g_x'] <= 25) )& # Low-fa
                (
                (recipes_df['fibre_g_x'] >= 5) |  # High-fiber
                (recipes_df['protein_g_x'] >= 15)  # High protein
                )
                ]

        # Select top 12 recommendations
        recipe_list = recommended_recipes[['RecipeName', 'TotalTimeInMins', 'Ingredients','Diet', 'TranslatedInstructions']].to_dict('records')

        # Pick 7 random recipes
        recommended_recipes = random.sample(recipe_list, 7)
        
        print(recommended_recipes)
        return Response({
            'recipes': recommended_recipes, 
            'is_diabetic': is_diabetic, 
            'has_cardio': has_cardio
        }, status=status.HTTP_200_OK)
    else:
        print("Errors:", serializer.errors)  # Print validation errors
        return Response({"errors": serializer.errors}, status=400)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def signup(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User created successfully!"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def complete_profile(request):
    """Complete user profile after signup."""
    try:
        user_profile, created = UserSerializer.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(user_profile, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully!"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_details(request):
    user = request.user
    return Response({"id": user.id, "username": user.username, "email": user.email})


from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

# Get the CustomUser model
User = get_user_model()

@api_view(["POST"])
def login_view(request):
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)  # Use CustomUser instead of default User model
    except User.DoesNotExist:
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=user.username, password=password)  # Authenticate with username
    if user is None:
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

    # Generate JWT token
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    return Response({
        "message": "Login successful",
        "token": access_token,
        "username": user.username  # Send username for frontend display
    }, status=status.HTTP_200_OK)


from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view


# ✅ Create or Update Profile
@api_view(['POST'])
def setup_profile(request):
    username = request.data.get('username')
    
    if not username:
        return Response({"error": "Username is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    profile, created = UserProfile.objects.update_or_create(
        username=username, defaults=request.data
    )
    
    return Response(
        {"message": "Profile created" if created else "Profile updated", "profile": UserProfileSerializer(profile).data},
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )

# ✅ Fetch Profile by Username
# @api_view(['GET'])
# def get_profile(request, username):
#     try:
#         profile = UserProfile.objects.get(username=username)
#         return Response(UserProfileSerializer(profile).data, status=status.HTTP_200_OK)
#     except UserProfile.DoesNotExist:
#         return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

# ✅ Update Profile
@api_view(['PUT'])
def update_profile(request, username):
    try:
        profile = UserProfile.objects.get(name=username)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated", "profile": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except UserProfile.DoesNotExist:
        return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def profile_setup(request):
    """API to handle user profile setup."""
    user = request.user

    try:
        # Check if profile exists or create a new one
        user_profile, created = UserProfile.objects.get_or_create(user=user)

        # Update fields from request data
        user_profile.goal = request.data.get('goal', user_profile.goal)
        user_profile.name = request.data.get('name', user_profile.name)
        user_profile.age = request.data.get('age', user_profile.age)
        user_profile.height = request.data.get('height', user_profile.height)
        user_profile.insulin = request.data.get('insulin', user_profile.insulin)
        user_profile.weight = request.data.get('weight', user_profile.weight)

        user_profile.save()

        return Response({"message": "Profile updated successfully!"}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
def get_user_profile(request):
    """API to get user profile details."""
    try:
        user_profile = UserProfile.objects.get(na)
        serializer = UserProfileSerializer(user_profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except UserProfile.DoesNotExist:
        return Response({"message": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(["GET"])
@permission_classes([IsAuthenticated])  # Ensure only authenticated users can access    
def get_choices(request):
    choices = {
        "gender_choices": UserProfile.GENDER_CHOICES,
        "health_choices": UserProfile.HEALTH_CHOICES,
        "physical_activity_choices": UserProfile.PHYSICAL_ACTIVITY_CHOICES,
        "diet_choices": UserProfile.DIET_CHOICE,
        "family_history_choices": UserProfile.FAMILY_HISTORY_CHOICES,
    }
    return JsonResponse(choices)

API_KEY= '80f8317fe9164e8a9951298d3009ff2e'
from django.views.decorators.csrf import csrf_exempt
import requests
from django.http import JsonResponse
cache = {}
import time
 
# def get_ingredient_substitutes(ingredient_name):
#     url = f"https://api.spoonacular.com/food/ingredients/substitutes?ingredientName={ingredient_name}&apiKey={API_KEY}"
#     response = requests.get(url)
#     if response.status_code == 200:
#         return response.json()
#     return {"error": "Failed to fetch substitutes"}

def get_ingredient_substitutes(ingredient_name):
    """Fetch substitutes for a given ingredient using Spoonacular API."""
    if ingredient_name in cache:
        print(f"🔁 Using cached substitutes for '{ingredient_name}'")
        return cache[ingredient_name]

    print(f"📦 Fetching substitutes for '{ingredient_name}'")
    url = f"https://api.spoonacular.com/food/ingredients/substitutes?ingredientName={ingredient_name}&apiKey={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        cache[ingredient_name] = data
        return data
    else:
        return {"error": f"Failed to fetch substitutes: {response.status_code}"}

# def get_recipes_with_ingredient(ingredient):
#     """Fetch recipes using the substitute ingredient with detailed info."""
#     if ingredient in cache:
#         print(f"🔁 Using cached recipes for '{ingredient}'")
#         return cache[ingredient]

#     print(f"🍽️  Fetching recipes with '{ingredient}'")
#     url = f"https://api.spoonacular.com/recipes/complexSearch?includeIngredients={ingredient}&addRecipeInformation=true&number=5&apiKey={API_KEY}"
#     response = requests.get(url)

#     if response.status_code == 200:
#         data = response.json()
#         cache[ingredient] = data
#         return data
#     else:
#         return {"error": f"Failed to fetch recipes: {response.status_code}"}

# def find_recipes_with_substitutes(original_ingredient):
#     substitutes_data = get_ingredient_substitutes(original_ingredient)

#     if "substitutes" not in substitutes_data:
#         print("❌ No substitutes found.")
#         return

#     for substitute in substitutes_data["substitutes"]:
#         recipes = get_recipes_with_ingredient(substitute)
        
#         print(f"\n📌 Recipes using '{substitute}' instead of '{original_ingredient}':\n")
        
#         if "results" in recipes:
#             for recipe in recipes["results"]:
#                 print(f"🍲 {recipe['title']}")
#                 print(f"   Ready in {recipe['readyInMinutes']} minutes | Servings: {recipe['servings']}")

#                 # 📝 Print instructions if available
#                 instructions = recipe.get("analyzedInstructions", [])
#                 if instructions and instructions[0].get("steps"):
#                     print("   📖 Instructions:")
#                     for step in instructions[0]["steps"]:
#                         print(f"     {step['number']}. {step['step']}")
#                 else:
#                     print("   ⚠️ Instructions not available in API response.")

#                 print()  # extra line
#         else:
#             print("⚠️ No recipes found.\n")

#         time.sleep(1)

# # Example run
# find_recipes_with_substitutes("butter")


@csrf_exempt
def ingredient_substitute_view(request):
    if request.method == "GET":
        ingredient_name = request.GET.get("ingredient", "")
        if not ingredient_name:
            return JsonResponse({"error": "Ingredient name is required"}, status=400)
        
        substitutes = get_ingredient_substitutes(ingredient_name)
        return JsonResponse(substitutes)
    
    return JsonResponse({"error": "Invalid request method"}, status=405)

from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Predefined ingredient substitution data
ingredient_subs = {
    "milk": ["almond milk", "soy milk", "oat milk", "coconut milk", "diluted cashew paste"],
    "butter": ["margarine", "coconut oil", "olive oil", "ghee"],
    "egg": ["chia seeds (1 tbsp + 3 tbsp water)", "flaxseed (1 tbsp + 3 tbsp water)", "unsweetened applesauce (1/4 cup)", "mashed banana (1/4 cup)"],
    "sugar": ["jaggery", "honey", "maple syrup", "stevia", "agave nectar"],
    "flour": ["almond flour", "coconut flour", "oat flour", "whole wheat flour"],
    "maida": ["whole wheat flour", "multigrain flour", "chickpea flour (for pakoras)", "semolina (for crispiness)"],
    "all purpose flour": ["whole wheat flour", "multigrain flour", "chickpea flour (for pakoras)", "semolina (for crispiness)"],
    "baking powder": ["1/4 tsp baking soda + 1/2 tsp cream of tartar"],
    "soy sauce": ["tamari", "coconut aminos", "Worcestershire sauce", "Maggi seasoning"],
    "lemon juice": ["lime juice", "white vinegar", "apple cider vinegar", "tamarind pulp (for Indian curries)"],
    "vinegar": ["lemon juice", "lime juice", "tamarind water"],
    "cream": ["evaporated milk", "Greek yogurt", "coconut cream", "malai (milk skin)"],
    "whipping cream": ["malai blended with milk", "chilled coconut cream", "hung curd (for savory dishes)"],
    "cornstarch": ["arrowroot powder", "tapioca starch", "rice flour", "gram flour (besan)"],
    "mayonnaise": ["1 egg+salt a pinch+oil 1tsp(3-4 tablespoons of mayonnaise)", "mashed avocado", "hung curd", "hummus"],
    "buttermilk": ["1 cup milk + 1 tbsp vinegar/lemon juice (sit 10 mins)", "diluted curd (1/2 cup curd + 1/2 cup water)"],
    "tomato sauce": ["tomato puree + pinch of sugar + pinch of salt", "tomato paste + water + sugar", "ketchup (in small amounts)"],
    "onion": ["leek", "shallots", "onion powder", "spring onions"],
    "garlic": ["garlic powder", "shallots", "chives", "hing (asafoetida, for Indian dishes)"],
    "chili powder": ["paprika + cumin", "cayenne pepper", "red chili powder", "hot sauce"],
    "chili flakes": [
      "dry roast whole red chilies and crush coarsely (homemade chili flakes)",
      "crushed Kashmiri red chili (for color and mild heat)",
      "red chili powder (use sparingly as it's finer and hotter)",
      "green chili paste (for fresh recipes)"
    ],
    "oil": ["butter", "ghee", "applesauce (for baking)", "Greek yogurt"],
    "cheese": ["nutritional yeast", "vegan cheese", "cottage cheese (paneer)"],
    "oregano": [
      "ajwain (carom seeds, for Indian curries)",
      "dried basil + dried thyme (1:1 mix)",
      "dried marjoram",
      "pizza masala"
    ],
    "sour cream": [
      "hung curd",
      "buttermilk",
      "blended cottage cheese (paneer)",
      "cream cheese thinned with milk"
    ],
    "hung curd": [
      "Greek yogurt",
      "strained regular curd",
      "labneh",
      "thick sour yogurt",
      "blended silken tofu (for vegan option)"
    ],
    "coriander powder": [
      "ground cumin (in lesser amount)",
      "fresh coriander (for garnishing only)",
      "curry powder (may alter taste slightly)",
      "caraway seeds (lightly crushed, use sparingly)"
    ],
    "garam masala": [
      "curry powder (adjust for sweetness/spice)",
      "homemade mix (equal parts cumin, coriander, cinnamon, cloves, cardamom)",
      "chana masala powder (in Indian dishes)",
      "tandoori masala (for smoky flavor)"
    ],
    "curd": [
      "Greek yogurt",
      "buttermilk",
      "hung curd",
      "blended silken tofu (for vegan option)",
      "coconut yogurt"
    ]
}

# # Load the SentenceTransformer model
# import tensorflow as tf
# import tensorflow_hub as hub

# # Load the model using TensorFlow Hub (if you're using TensorFlow)
# embed = hub.load("https://tfhub.dev/google/all-miniLM-l6-v2/2")


# # Convert ingredients into a list of strings
# ingredients = list(ingredient_subs.keys())
# substitutes = [sub for subs in ingredient_subs.values() for sub in subs]

# # Function to embed texts using TensorFlow Hub model
# def get_embeddings(texts):
#     return embed(texts).numpy()

# # Embed the ingredients and their substitutes
# ingredient_embeddings = get_embeddings(ingredients)
# substitute_embeddings = get_embeddings(substitutes)

# # Function to find the most similar ingredient substitutes
# def find_similar_ingredients(query):
#     # Embed the query ingredient
#     query_embedding = get_embeddings([query])

#     # Calculate cosine similarity between the query and all ingredients
#     cosine_similarities = cosine_similarity(query_embedding, ingredient_embeddings)

#     # Get the index of the most similar ingredient
#     most_similar_idx = np.argmax(cosine_similarities)

#     # Get the closest ingredient
#     closest_ingredient = ingredients[most_similar_idx]

#     # Get the corresponding substitutes for that ingredient
#     closest_substitutes = ingredient_subs[closest_ingredient]

#     return closest_ingredient, closest_substitutes

@csrf_exempt
def ingredient_substitute_views(request):
    if request.method == 'GET':
        # Get ingredient from the query params
        ingredient = request.GET.get('ingredient', '').lower()

        if not ingredient:
            return JsonResponse({"error": "Ingredient is required."}, status=400)

        # Find the closest ingredient and its substitutes
        closest_ingredient, substitutes = find_similar_ingredients(ingredient)

        # Return the result as JSON
        return JsonResponse({
            "ingredient": closest_ingredient,
            "substitutes": substitutes
        })
    else:
        return JsonResponse({"error": "Invalid HTTP method. Use GET."}, status=405)

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

ingredients = list(ingredient_subs.keys())

vectorizer = TfidfVectorizer()
ingredient_vectors = vectorizer.fit_transform(ingredients)

def find_similar_ingredients(query):
    query_vector = vectorizer.transform([query])
    similarity = cosine_similarity(query_vector, ingredient_vectors).flatten()
    idx = np.argmax(similarity)
    closest_ingredient = ingredients[idx]
    return closest_ingredient, ingredient_subs[closest_ingredient]
