def get_keys_with_pattern(pattern):
    redis_conn = get_redis_connection("default")
    keys = []
    cursor = "0"
    while cursor != 0:
        cursor, found_keys = redis_conn.scan(cursor=cursor, match=pattern)
        keys.extend(found_keys)
    return keys
