import secrets


def generate_key():
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"SECRET_KEY={secrets.token_hex(64)}")


if __name__ == "__main__":
    generate_key()
