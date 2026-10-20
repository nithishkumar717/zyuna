"""
Zyuna root launcher - forwards execution to bot/zyuna.py
"""
import sys
import os

root_dir = os.path.dirname(os.path.abspath(__file__))
bot_dir = os.path.join(root_dir, "bot")
bot_main = os.path.join(bot_dir, "zyuna.py")

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if bot_dir not in sys.path:
    sys.path.insert(0, bot_dir)

if os.path.isfile(bot_main):
    with open(bot_main, "rb") as f:
        code = compile(f.read(), bot_main, "exec")
        exec(code, globals())
else:
    print(f"Error: Could not locate {bot_main}")
