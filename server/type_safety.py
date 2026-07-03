def safe_int(v):
    try:
        return int(float(v))
    except:
        return None


def safe_float(v):
    try:
        return float(v)
    except:
        return None