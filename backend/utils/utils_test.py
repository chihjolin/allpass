import os
from pathlib import Path

current_path = Path(__file__).resolve()
db_path = current_path.parents[2] / "mock" / "database.json"
print(db_path)

current_path = Path(__file__).resolve()
index_folder = current_path.parents[1] / "frontend" / "static" 
print(index_folder)
