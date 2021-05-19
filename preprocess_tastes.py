"""
Helper script to be run ad hoc. Performs one-time preprocessing on the cached
list of taste-related keywords.
"""

TASTES_KEYWORDS = "tastes_keywords.txt"

def read_in_uniques(filename: str) -> list:
    """Return the list from the text file. Ignore duplicate elements."""
    seen = set()
    lines_list = []
    with open(filename, "r") as fobj:
        for line in fobj.readlines():
            line = line.lower().strip() # Make lowercase and strip any leading or trailing whitespace chars
            if not line in seen:
                seen.add(line)
                lines_list.append(line + "\n") # Add back exactly one newline
    return lines_list

def is_unique_elements(input_list: list):
    """Returns True if there are no duplicate elements in the list, else False."""
    seen = set()
    for word in input_list:
        if not word in seen:
            seen.add(word)
        else:
            return False
    return True

def write_out(filename: str, lines: list):
    with open(filename, "w") as fobj:
        fobj.writelines(lines)


def main():
    lines = read_in_uniques(TASTES_KEYWORDS)
    print(lines)
    lines.sort() # sort lexicographically
    print(lines)
    write_out(filename=TASTES_KEYWORDS, lines=lines)
    

if __name__ == "__main__":
    main()