

def settings(roles):
    if "admin" in roles:
        return "Admin settings"
    elif "user" in roles:
        return "User settings"
    return "No specific settings available"