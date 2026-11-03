import re
with open("tornadoes_2025.json", "r") as f:
    text = f.read()

matches = re.finditer(r'.{0,100}hailstone.{0,100}', text, re.IGNORECASE)
for m in matches:
    print(m.group(0))
