import operator


# Return a dict with key = [admin]; value = [count of administrable]
def getCountValueFromKey(data, interested_key, sortOrder=True):
    if data is None:
        return None
    # create a list with all keys and create a dict initialized with previous keys and 0
    keys = list(map(lambda x: x[interested_key], data))
    final_res = dict.fromkeys(keys, 0)

    # compute number of occurence in real data
    for elem in data:
        final_res[elem[interested_key]] += 1
    final_res = dict(
        sorted(final_res.items(), key=operator.itemgetter(1), reverse=sortOrder)
    )
    return final_res


# Return a dict with key = [admin]; value = [list of administrable]
def getListAdminTo(data, administrator_key, administrated_key, sortOrder=True):
    if data is None:
        return None
    # create a list with all keys and create a dict initialized with previous keys and empty list
    keys = list(map(lambda x: x[administrator_key], data))
    final_res = {}
    [final_res.setdefault(x, []) for x in keys]

    # compute number of occurence in real data
    for elem in data:
        final_res[elem[administrator_key]].append(elem[administrated_key])
    return final_res
