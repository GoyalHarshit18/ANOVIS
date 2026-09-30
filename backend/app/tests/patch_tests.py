import os
import glob
import re

tests_dir = r'c:\Users\hp\OneDrive\Desktop\ps170\backend\app\tests'
test_files = glob.glob(os.path.join(tests_dir, 'test_*.py'))

patterns = [
    r'(?m)^engine = create_engine.*?\n',
    r'(?m)^SQLALCHEMY_DATABASE_URL = .*?\n',
    r'(?m)^TestingSessionLocal = .*?\n',
    r'(?m)^Base\.metadata\.create_all\(bind=engine\)\n',
    r'(?ms)^def override_get_db\(\).*?db\.close\(\)\n\n?',
    r'(?m)^app\.dependency_overrides\[get_db\] = override_get_db\n',
    r'(?m)^client = TestClient\(app\)\n',
    r'(?ms)^@pytest\.fixture.*?def clean_db\(\).*?yield\n\n?',
    r'(?ms)^def get_test_db\(\).*?db\.close\(\)\n\n?',
    r'(?m)^Base\.metadata\.drop_all\(bind=engine\)\n',
]

for filepath in test_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    for p in patterns:
        content = re.sub(p, '', content)

    # Convert def test_xyz() to def test_xyz(client, db)
    new_lines = []
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('def test_') and '()' in line:
            func_body = '\n'.join(lines[i+1:i+100])
            args = []
            if 'client' in func_body: args.append('client')
            if 'db' in func_body or 'TestingSessionLocal' in func_body: args.append('db')
            if args:
                line = line.replace('()', f'({", ".join(args)})')
        
        line = line.replace('TestingSessionLocal()', 'db')
        new_lines.append(line)
        i += 1

    content = '\n'.join(new_lines)
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched {os.path.basename(filepath)}")
