# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import sys
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from it_support_agent.agent import app

# Load environment variables from the .env file and override any system defaults
load_dotenv(override=True)

# Initialize the InMemoryRunner with our IT Support App
runner = InMemoryRunner(app=app)

async def main():
    # Allow executing with a custom query from command line, otherwise use a default
    query = sys.argv[1] if len(sys.argv) > 1 else "My laptop is running very slowly and my apps are freezing."
    
    print(f"==================================================")
    print(f"Starting IT Support Agent Workflow")
    print(f"Query: {query}")
    print(f"==================================================")
    
    try:
        # run_debug runs the agent workflow and streams/logs intermediate events.
        # It requires ADK Python 1.18.0 or higher.
        response = await runner.run_debug(query)
        print(f"\n==================================================")
        print(f"Final Agent Recommendation:")
        print(f"==================================================")
        print(response)
    except Exception as e:
        print(f"\nExecution failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
