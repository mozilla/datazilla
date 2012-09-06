import json

def jstr(obj):
    """Shortcut to printing out an obj as formatted json."""
    return json.dumps(obj, indent=4)