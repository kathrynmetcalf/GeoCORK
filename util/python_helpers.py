def search_dictionary(dictionary: dict, target_value):
    """
    Search a nested dictionary for a target value.
    :param dictionary:
    :param target_value:
    :return:
    """
    if not isinstance(dictionary, dict):
        return False

    def search_nested_dict(search_dict):
        for key, value in search_dict.items():
            if key == target_value:
                return True
            elif isinstance(value, dict):
                if search_nested_dict(value):
                    return True
            else:
                if value == target_value:
                    return True
        return False

    return search_nested_dict(dictionary)