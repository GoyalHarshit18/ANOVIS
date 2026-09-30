import os, glob

test_files = glob.glob('app/tests/test_*.py')
for tf in test_files:
    with open(tf, 'r') as f:
        content = f.read()

    content = content.replace('\"sqlite:///./test.db\"', '\"sqlite:///:memory:\"')
    content = content.replace('f\"sqlite:///{db_path}\"', '\"sqlite:///:memory:\"')
    content = content.replace('f\"sqlite:///{db_file}\"', '\"sqlite:///:memory:\"')

    if 'from sqlalchemy.pool import StaticPool' not in content:
        content = content.replace('from sqlalchemy import create_engine', 'from sqlalchemy import create_engine\nfrom sqlalchemy.pool import StaticPool')
    
    content = content.replace('connect_args={\"check_same_thread\": False}', 'connect_args={\"check_same_thread\": False}, poolclass=StaticPool')
    
    with open(tf, 'w') as f:
        f.write(content)
print('Done!')
