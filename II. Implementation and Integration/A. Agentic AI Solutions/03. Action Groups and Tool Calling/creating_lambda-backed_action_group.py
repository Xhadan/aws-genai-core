import boto3

bedrock_agent = boto3.client('bedrock-agent')

# OpenAPI schema defining available actions
api_schema = '''
openapi: 3.0.0
info:
  title: Order Management API
  version: 1.0.0
  description: API for managing customer orders
paths:
  /orders/{orderId}:
    get:
      operationId: getOrderStatus
      summary: Get the current status of an order
      description: |
        Retrieves detailed status information for a specific order.
        Use this when the user asks about their order status, delivery,
        or wants to track a shipment. Returns order details including
        status, items, and estimated delivery date.
      parameters:
        - name: orderId
          in: path
          required: true
          description: The unique order identifier (e.g., ORD-12345)
          schema:
            type: string
      responses:
        "200":
          description: Order details
          content:
            application/json:
              schema:
                type: object
                properties:
                  orderId:
                    type: string
                  status:
                    type: string
                    enum: [pending, processing, shipped, delivered]
                  items:
                    type: array
                    items:
                      type: object
                  estimatedDelivery:
                    type: string
  /orders:
    post:
      operationId: createOrder
      summary: Create a new order
      description: |
        Creates a new order for the customer. Use this when the user
        wants to place an order or purchase items. Requires product IDs
        and quantities. Returns the new order ID and confirmation.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - items
                - shippingAddress
              properties:
                items:
                  type: array
                  description: List of items to order
                  items:
                    type: object
                    properties:
                      productId:
                        type: string
                      quantity:
                        type: integer
                shippingAddress:
                  type: string
                  description: Full shipping address
      responses:
        "201":
          description: Order created successfully
'''

# Create the action group
response = bedrock_agent.create_agent_action_group(
    agentId='AGENT123',
    agentVersion='DRAFT',
    actionGroupName='order-management',
    description='Manage customer orders - check status, create orders, process returns',
    actionGroupExecutor={
        'lambda': 'arn:aws:lambda:us-east-1:123456789012:function:order-management'
    },
    apiSchema={
        'payload': api_schema
    },
    actionGroupState='ENABLED'
)