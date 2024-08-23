import json
import os
__BD_Folders__ = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'DB')

Files = {
    'application': 'Application.json',
    'bank_history': 'bank_history.json',
    'bank_history_conf': 'Bank_History_Reader.json',
    'criteria': 'Criterial_2.json',
}


def load_Json(json_File):
    File_Name =  os.path.join(__BD_Folders__, json_File)
    with open(File_Name, 'r') as file:
        return json.load(file)

def save_Json(Change, json_File):
    File_Name =  os.path.join(__BD_Folders__, json_File)
    with open(File_Name, 'w') as file:
        json.dump(Change, file, indent=2)

def update_Json(key, value, json_File):
    File_Name =  os.path.join(__BD_Folders__, json_File)
    Json = load_Json(File_Name)
    keys = key.split('.')
    current = Json
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    current[keys[-1]] = value
    save_Json(Json, json_File)
