regexesConfig=[
    {
        'name': 'Internal Ticket',
        'description': 'Block internal JIRA tickets',
        'pattern': r'PROJ-\d{4,6}',
        'action': 'BLOCK'
    }
]