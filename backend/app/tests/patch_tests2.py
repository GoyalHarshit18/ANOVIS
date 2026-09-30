import os
import glob
import re

tests_dir = r'c:\Users\hp\OneDrive\Desktop\ps170\backend\app\tests'
test_files = glob.glob(os.path.join(tests_dir, 'test_*.py'))

for filepath in test_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove all `db = db`
    content = re.sub(r'(?m)^\s*db = db\n', '', content)
    # Remove all `db.close()`
    content = re.sub(r'(?m)^\s*db\.close\(\)\n', '', content)
    # Remove `session.close()` just in case
    content = re.sub(r'(?m)^\s*session\.close\(\)\n', '', content)

    new_lines = []
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('def test_') and '(' in line:
            func_name = line.split('(')[0]
            args_str = line.split('(')[1].split(')')[0]
            args = [a.strip() for a in args_str.split(',') if a.strip()]
            
            # Look ahead for `db` usage
            func_body = '\n'.join(lines[i+1:i+100])
            # Only add `db` if `db` as a token is used in the body, or `session` if `session = db`
            uses_db = bool(re.search(r'\bdb\b', func_body))
            if uses_db and 'db' not in args:
                args.append('db')
                
            uses_client = bool(re.search(r'\bclient\b', func_body))
            if uses_client and 'client' not in args:
                args.insert(0, 'client')
            
            args_join = ", ".join(args)
            line = f"{func_name}({args_join}):"
        
        new_lines.append(line)
        i += 1

    content = '\n'.join(new_lines)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Fixed args in {os.path.basename(filepath)}')
