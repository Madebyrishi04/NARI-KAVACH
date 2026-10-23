def send_sms(phone_number: str, message: str):
    """
    Development SMS service.

    This currently simulates sending an SMS.
    No real SMS or money is involved.
    """

    print("\n========== SMS SIMULATION ==========")
    print(f"To: {phone_number}")
    print(f"Message: {message}")
    print("Status: SMS simulated successfully")
    print("====================================\n")

    return {
        "success": True,
        "status": "simulated",
        "phone_number": phone_number
    }