def combine_dict_items(data_dict):
    combined_list = []
    for key in data_dict:
        combined_list.extend(data_dict[key])
    return combined_list
