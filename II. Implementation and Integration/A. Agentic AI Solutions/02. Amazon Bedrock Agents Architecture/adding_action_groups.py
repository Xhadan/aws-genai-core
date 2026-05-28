# Step 2: Create action group for flight search
action_group_response = bedrock_agent.create_agent_action_group(
    agentId=agent_id,
    agentVersion='DRAFT',
    actionGroupName='flight-search',
    description='Search for available flights',
    actionGroupExecutor={
        'lambda': 'arn:aws:lambda:us-east-1:123456789012:function:search-flights'
    },
    apiSchema={
        'payload': '''
        openapi: 3.0.0
        info:
          title: Flight Search API
          version: 1.0.0
        paths:
          /search-flights:
            post:
              operationId: searchFlights
              description: Search for available flights between cities
              requestBody:
                required: true
                content:
                  application/json:
                    schema:
                      type: object
                      required:
                        - origin
                        - destination
                        - date
                      properties:
                        origin:
                          type: string
                          description: Origin airport code (e.g., JFK)
                        destination:
                          type: string
                          description: Destination airport code (e.g., LAX)
                        date:
                          type: string
                          description: Travel date (YYYY-MM-DD)
                        passengers:
                          type: integer
                          description: Number of passengers
              responses:
                "200":
                  description: List of available flights
        '''
    }
)