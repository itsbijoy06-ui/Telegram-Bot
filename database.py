import datetime

users = {}

def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "balance": 0,
            "orders": [],
            "transactions": [],
            "first_name": "User",
            "username": ""
        }
    return users[user_id]

def update_user_info(user_id, username, name):
    user = get_user(user_id)
    user["username"] = username
    user["first_name"] = name

def get_balance(user_id):
    return get_user(user_id)["balance"]

def add_balance(user_id, amount, note="Deposit"):
    user = get_user(user_id)
    user["balance"] += amount

    user["transactions"].append({
        "type": "credit",
        "amount": amount,
        "note": note,
        "time": str(datetime.datetime.now())
    })

    return user["balance"]

def deduct_balance(user_id, amount, note="Order"):
    user = get_user(user_id)

    if user["balance"] < amount:
        return False, user["balance"]

    user["balance"] -= amount

    user["transactions"].append({
        "type": "debit",
        "amount": amount,
        "note": note,
        "time": str(datetime.datetime.now())
    })

    return True, user["balance"]

def add_order(user_id, order_data):
    user = get_user(user_id)
    user["orders"].append(order_data)

def update_order_status(user_id, order_id, status):
    user = get_user(user_id)

    for order in user["orders"]:
        if order["order_id"] == order_id:
            order["status"] = status
            return True

    return False

def get_orders(user_id):
    return get_user(user_id)["orders"]

def get_all_users():
    return users
