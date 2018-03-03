import re

def space_clean(text):
    pattern = r" {2,}"
    repl = " "
    return re.sub(pattern, repl, text)

def html_clean(text):
    pattern = r"<br */>"
    repl = ""
    return re.sub(pattern, repl, text.strip())

class DisruptionMessage:
    def  __init__(self, mod_date, text):
        self.mod_date = mod_date
        self.text = html_clean(text)

def merge_messages(old, new):
    merged = old + new
    merged.sort(key=lambda entry: entry.mod_date)
    result = [merged[0]]
    for i in enumerate(1, merged.size()):
        first = merged[i-1]
        second = merged[i]
        if first.mod_date != second.mod_date:
            result.append(second)
    return result
