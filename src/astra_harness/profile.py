"""Public profiles describe disabled integrations; they cannot enable them."""
DEFAULT_PROFILE = {
    "schema": 1,
    "purpose": "synthetic research only",
    "integrations": {"observation": False, "training": False,
                     "automatic_maintenance": False, "cloud": False},
}


def validate_profile(value):
    if not isinstance(value, dict) or set(value) != set(DEFAULT_PROFILE):
        raise ValueError("Unsupported research profile fields")
    if type(value['schema']) is not int or value['schema'] != 1 or not isinstance(value['purpose'], str) or value['purpose'] != DEFAULT_PROFILE['purpose']:
        raise ValueError("Unsupported research profile")
    if not isinstance(value['integrations'], dict) or set(value['integrations']) != set(DEFAULT_PROFILE['integrations']) or any(flag is not False for flag in value['integrations'].values()):
        raise ValueError("Private integrations are not included in this public core")
    return value
