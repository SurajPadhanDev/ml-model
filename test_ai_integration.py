import os
import sys
import argparse
from PIL import Image
from dotenv import load_dotenv
import asyncio

# Import the AI integration module
try:
    from ai_integration import check_api_availability, classify_with_gemini, classify_with_openai
except ImportError:
    print("Error: ai_integration.py module not found. Make sure it's in the current directory.")
    sys.exit(1)

# Load environment variables
load_dotenv()

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test AI integration for waste classification')
    parser.add_argument('image_path', help='Path to the image file to classify')
    parser.add_argument('--api', choices=['gemini', 'openai', 'both'], default='both',
                        help='Which API to use for classification')
    args = parser.parse_args()
    
    # Check if the image file exists
    if not os.path.exists(args.image_path):
        print(f"Error: Image file '{args.image_path}' not found.")
        sys.exit(1)
    
    # Open the image
    try:
        image = Image.open(args.image_path)
        print(f"Loaded image: {args.image_path} ({image.width}x{image.height})")
    except Exception as e:
        print(f"Error opening image: {str(e)}")
        sys.exit(1)
    
    # Check API availability
    api_status = check_api_availability()
    print("\nAPI Status:")
    print(f"  Gemini API: {'Available' if api_status['gemini'] else 'Not configured'}")
    print(f"  OpenAI API: {'Available' if api_status['openai'] else 'Not configured'}")
    print()
    
    # Classify with selected APIs
    results = []
    
    # Use Gemini API
    if (args.api == 'gemini' or args.api == 'both') and api_status['gemini']:
        print("Classifying with Gemini API...")
        try:
            gemini_result = await classify_with_gemini(image)
            print("\nGemini API Result:")
            if "error" in gemini_result:
                print(f"  Error: {gemini_result['error']}")
            else:
                print(f"  Category: {gemini_result['class_name']}")
                print(f"  Confidence: {gemini_result['confidence']:.2f}")
                print(f"  Reasoning: {gemini_result['reasoning']}")
                results.append(gemini_result)
        except Exception as e:
            print(f"  Error with Gemini API: {str(e)}")
    elif args.api == 'gemini' and not api_status['gemini']:
        print("Error: Gemini API is not configured. Set GEMINI_API_KEY in .env file.")
    
    # Use OpenAI API
    if (args.api == 'openai' or args.api == 'both') and api_status['openai']:
        print("\nClassifying with OpenAI API...")
        try:
            openai_result = classify_with_openai(image)
            print("\nOpenAI API Result:")
            if "error" in openai_result:
                print(f"  Error: {openai_result['error']}")
            else:
                print(f"  Category: {openai_result['class_name']}")
                print(f"  Confidence: {openai_result['confidence']:.2f}")
                print(f"  Reasoning: {openai_result['reasoning']}")
                results.append(openai_result)
        except Exception as e:
            print(f"  Error with OpenAI API: {str(e)}")
    elif args.api == 'openai' and not api_status['openai']:
        print("Error: OpenAI API is not configured. Set OPENAI_API_KEY in .env file.")
    
    # Show combined result if we have multiple results
    if len(results) > 1:
        print("\nCombined Result:")
        best_result = max(results, key=lambda x: x.get("confidence", 0))
        print(f"  Best Category: {best_result['class_name']} (from {best_result['source']})")
        print(f"  Confidence: {best_result['confidence']:.2f}")
        print(f"  Reasoning: {best_result['reasoning']}")

if __name__ == "__main__":
    asyncio.run(main())