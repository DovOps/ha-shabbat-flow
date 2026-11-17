"""Repository hygiene gate; a human content review is still required."""
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
files=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
patterns={
    'absolute workstation path':re.compile(r'/(?:Users|home)/[A-Za-z0-9_.-]+/'),
    'Windows workstation path':re.compile(r'[A-Za-z]:\\Users\\[^\\]+\\'),
    'private network address':re.compile(r'\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'),
    'credential-shaped string':re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,})'),
    'personal document URL':re.compile(r'docs\.google\.com/(?:document|spreadsheets)/d/[A-Za-z0-9_-]{20,}'),
}
failures=[]
for name in files:
    if not name:continue
    path=ROOT/name
    if name.startswith(('.specify/scripts/','.specify/templates/','docs/vendor/')):continue
    if path.suffix in ('.png','.webp','.jpg'):continue
    try:text=path.read_text()
    except UnicodeDecodeError:
        failures.append((name,'unexpected binary'));continue
    for label,pattern in patterns.items():
        if pattern.search(text):failures.append((name,label))
    if path.suffix in ('.db','.sqlite','.pem','.key') or path.name.startswith('.env'):
        failures.append((name,'private file type'))
if failures:
    for name,label in failures:print(f'{name}: {label}')
    sys.exit(1)
print('Repository hygiene checks passed. Review genericized examples and staged diff before publishing.')
