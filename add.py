file_name = "wordlist/100000.txt"
string_to_add = "admin:"

with open(file_name, 'r') as f:
    file_lines = [''.join([string_to_add, x.strip(), '\n']) for x in f.readlines()]

with open(file_name, 'w') as f:
    f.writelines(file_lines)
