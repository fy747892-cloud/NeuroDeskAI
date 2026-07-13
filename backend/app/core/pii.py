def mask_email(email: str) -> str:
    local_part, _, domain = email.partition("@")
    if not domain:
        return "***"
    visible = local_part[:1] or "*"
    return f"{visible}***@{domain}"


def mask_phone(phone: str) -> str:
    digits = "".join(char for char in phone if char.isdigit())
    if len(digits) <= 4:
        return "***"
    return f"***{digits[-4:]}"
