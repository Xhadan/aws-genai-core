'authConfig': {
    'type': 'OAUTH2',
    'clientId': '{{secretsmanager:salesforce-client-id}}',
    'clientSecret': '{{secretsmanager:salesforce-client-secret}}',
    'tokenEndpoint': 'https://login.salesforce.com/services/oauth2/token',
    'scopes': ['api', 'refresh_token']
}