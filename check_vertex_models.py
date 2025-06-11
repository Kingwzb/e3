#!/usr/bin/env python3
"""
Script to check available Vertex AI models and help fix configuration issues.
"""

import asyncio
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings
from app.utils.logging import logger

# Common model names and their variations
COMMON_MODELS = [
    "gemini-1.5-pro-002",
    "gemini-1.5-pro",
    "gemini-1.5-flash-002", 
    "gemini-1.5-flash",
    "gemini-1.0-pro-001",
    "gemini-1.0-pro",
    "gemini-pro",
    "text-bison",
    "text-bison-001"
]

# Common regions where Vertex AI is available
COMMON_REGIONS = [
    "us-central1",
    "us-east1", 
    "us-west1",
    "europe-west1",
    "europe-west4",
    "asia-southeast1",
    "asia-northeast1"
]

async def test_model_availability(project_id: str, location: str, model: str):
    """Test if a specific model is available in a region."""
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        # Log detailed parameters before vertexai.init call
        init_params = {
            "project": project_id,
            "location": location
        }
        logger.info(f"VERTEXAI_INIT_CALL [Test Script]: Calling vertexai.init with parameters: {init_params}")
        logger.info(f"VERTEXAI_INIT_CALL [Test Script]: project={project_id}, location={location}")
        logger.info(f"VERTEXAI_INIT_CALL [Test Script]: model_to_test={model}")
        logger.info(f"VERTEXAI_INIT_CALL [Test Script]: test_purpose=model_availability_check")
        
        # Initialize Vertex AI for this region
        vertexai.init(project=project_id, location=location)
        
        # Try to create the model
        test_model = GenerativeModel(model)
        
        # Try a simple generation to verify it works
        response = await test_model.generate_content_async(
            "Hello",
            generation_config={"max_output_tokens": 10}
        )
        
        return True, "Available"
        
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "not found" in error_msg.lower():
            return False, "Not found"
        elif "403" in error_msg or "permission" in error_msg.lower():
            return False, "Permission denied"
        else:
            return False, f"Error: {error_msg[:100]}..."

def print_current_config():
    """Print current Vertex AI configuration."""
    print("🔧 Current Vertex AI Configuration:")
    print(f"   Project ID: {settings.vertexai_project_id}")
    print(f"   Location: {settings.vertexai_location}")
    print(f"   Model: {settings.vertexai_model}")
    print(f"   Credentials: {'✅ Set' if settings.google_application_credentials else '❌ Not set'}")
    print()

async def check_current_config():
    """Check if current configuration works."""
    print("🔍 Testing Current Configuration...")
    
    success, message = await test_model_availability(
        settings.vertexai_project_id,
        settings.vertexai_location, 
        settings.vertexai_model
    )
    
    if success:
        print(f"✅ Current config works: {settings.vertexai_model} in {settings.vertexai_location}")
        return True
    else:
        print(f"❌ Current config failed: {message}")
        return False

async def find_working_combinations():
    """Find working model/region combinations."""
    print("🔍 Searching for working model/region combinations...")
    print("This may take a few minutes...\n")
    
    working_combinations = []
    
    # Test current region first with different models
    print(f"Testing models in current region ({settings.vertexai_location}):")
    for model in COMMON_MODELS:
        print(f"  Testing {model}...", end=" ")
        success, message = await test_model_availability(
            settings.vertexai_project_id,
            settings.vertexai_location,
            model
        )
        
        if success:
            print("✅ Available")
            working_combinations.append((settings.vertexai_location, model))
        else:
            print(f"❌ {message}")
    
    # If no models work in current region, test other regions
    if not working_combinations:
        print(f"\nNo models found in {settings.vertexai_location}. Testing other regions...")
        
        for region in COMMON_REGIONS:
            if region == settings.vertexai_location:
                continue  # Already tested
                
            print(f"\nTesting region {region}:")
            for model in COMMON_MODELS[:3]:  # Test fewer models for other regions
                print(f"  Testing {model}...", end=" ")
                success, message = await test_model_availability(
                    settings.vertexai_project_id,
                    region,
                    model
                )
                
                if success:
                    print("✅ Available")
                    working_combinations.append((region, model))
                    break  # Found one working model in this region
                else:
                    print(f"❌ {message}")
    
    return working_combinations

def suggest_configuration(working_combinations):
    """Suggest the best configuration based on working combinations."""
    if not working_combinations:
        print("\n❌ No working combinations found!")
        print("\nPossible issues:")
        print("1. Vertex AI API not enabled in your project")
        print("2. Insufficient permissions")
        print("3. Project doesn't have access to Gemini models")
        print("4. Billing not enabled")
        print("\nTry these steps:")
        print("1. Enable Vertex AI API: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com")
        print("2. Check billing: https://console.cloud.google.com/billing")
        print("3. Verify permissions in IAM")
        return
    
    print(f"\n✅ Found {len(working_combinations)} working combinations!")
    print("\nRecommended configurations:")
    
    # Prefer current region if available
    current_region_combos = [combo for combo in working_combinations if combo[0] == settings.vertexai_location]
    
    if current_region_combos:
        print(f"\n🎯 Best option (current region {settings.vertexai_location}):")
        region, model = current_region_combos[0]
        print(f"   VERTEXAI_LOCATION={region}")
        print(f"   VERTEXAI_MODEL={model}")
    else:
        print(f"\n🎯 Best option (different region):")
        region, model = working_combinations[0]
        print(f"   VERTEXAI_LOCATION={region}")
        print(f"   VERTEXAI_MODEL={model}")
    
    print(f"\nAll working combinations:")
    for i, (region, model) in enumerate(working_combinations, 1):
        print(f"   {i}. {model} in {region}")

async def main():
    """Main function."""
    print("🚀 Vertex AI Model Checker")
    print("=" * 50)
    
    print_current_config()
    
    # Check if current config works
    if await check_current_config():
        print("🎉 Your current configuration is working!")
        return 0
    
    # Find working combinations
    working_combinations = await find_working_combinations()
    
    # Suggest configuration
    suggest_configuration(working_combinations)
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 