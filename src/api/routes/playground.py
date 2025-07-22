"""
Playground routes for FPT University Agent
"""

from agno.playground import Playground

######################################################
## Routes for the Playground Interface
######################################################

def create_playground_router(agent):
    """Create playground router with agent"""
    # Create a playground instance with the agent
    playground = Playground(agents=[agent])
    return playground.get_async_router() 