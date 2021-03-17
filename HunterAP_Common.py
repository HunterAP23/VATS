import configparser as confp


def print_dict(item, tablevel=1):
    types = [int, float, bool, str]
    for key, val in item.items():
        iter = None
        if type(val) == dict:
            print("{0}{1}".format("\t" * (tablevel - 1), key))
            iter = val
        elif type(val) in types or val is None:
            print("{0}{1}: {2}".format("\t" * tablevel, str(key).ljust(10), val))
            continue
        else:
            print("{0}{1}".format("\t" * (tablevel - 1), key))
            iter = vars(val)

        for k, v in iter.items():
            if type(v) == dict or type(v) == confp.SectionProxy:
                print("{0}{1}".format("\t" * tablevel, k))
                print_dict(v, tablevel + 1)
            elif type(v) == list:
                print("{0}{1}".format("\t" * tablevel, k))
                for i in v:
                    print("{0}{1}".format("\t" * (tablevel + 1), i))
            else:
                print("{0}{1}: {2}".format("\t" * tablevel, str(k).ljust(10), v))
