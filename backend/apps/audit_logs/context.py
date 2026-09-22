import threading

_local = threading.local()


def set_current_request(user, ip_address):
    _local.user = user
    _local.ip_address = ip_address


def get_current_user():
    return getattr(_local, "user", None)


def get_current_ip():
    return getattr(_local, "ip_address", None)


def clear_current_request():
    _local.user = None
    _local.ip_address = None
