def find(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return None


def redact(string, redact=False):
    return "REDACTED" if redact else string

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
