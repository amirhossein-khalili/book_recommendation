def remove_duplicates(dict_list):
    seen = set()
    unique_list = []
    for d in dict_list:
        # Convert the dictionary to a frozenset of tuples (which is hashable)
        t = frozenset(d.items())
        if t not in seen:
            seen.add(t)
            unique_list.append(d)
    return unique_list
