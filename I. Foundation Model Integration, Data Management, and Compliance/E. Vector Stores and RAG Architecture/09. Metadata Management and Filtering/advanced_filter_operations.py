# Numeric comparison
numeric_filter = {
    'filter': {
        'greaterThan': {
            'key': 'version',
            'value': 2.0
        }
    }
}

# Less than or equal
range_filter = {
    'filter': {
        'lessThanOrEquals': {
            'key': 'year',
            'value': 2024
        }
    }
}

# String list contains (IN operator)
list_filter = {
    'filter': {
        'in': {
            'key': 'department',
            'value': ['engineering', 'product', 'design']
        }
    }
}

# String list contains any (tags overlap)
tags_filter = {
    'filter': {
        'listContains': {
            'key': 'tags',
            'value': 'security'
        }
    }
}

# NOT operator
not_filter = {
    'filter': {
        'notEquals': {
            'key': 'status',
            'value': 'archived'
        }
    }
}

# Complex nested filter
complex_filter = {
    'filter': {
        'andAll': [
            {
                'orAll': [
                    {'equals': {'key': 'department', 'value': 'engineering'}},
                    {'equals': {'key': 'department', 'value': 'security'}}
                ]
            },
            {'equals': {'key': 'is_current', 'value': True}},
            {'greaterThanOrEquals': {'key': 'version', 'value': 1.0}}
        ]
    }
}