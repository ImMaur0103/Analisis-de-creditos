from fastapi import FastAPI, Header, HTTPException, Depends
from typing import Annotated
from pydantic import BaseModel
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os 
# Own Modules
from Modulos.PDF.PDF import OBJ_PDF
from Modulos.Query.Connector import load_Json, update_Json, Files

#---------------------------------------------------------------------------------------
#---------------------------------------------------------------- Descriptions ---------
Important_Info = """Return information From the DB\n
This info includes Personal Information and business information, Criteria and etc.
"""

#---------------------------------------------------------------------------------------
#---------------------------------------------------------------- Models ---------------
class InformationModel(BaseModel):
    info_request: str


#---------------------------------------------------------------------------------------
#--------------------------------------- Start APP -------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
save_dir = os.path.join(current_dir, 'files_save')

app = FastAPI(
    title="Credit Analysis API",
    description="API for analyzing credit applications",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tudominio.com", "http://localhost"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)

Start_info = (app.title + '\n' + app.description + '\n' + app.version)

async def validate_accept(accept: Annotated[str | None, Header()] = None):
    if "application/json" not in accept:
        raise HTTPException(status_code=406, detail="Only application/json is supported")

print(Start_info)

#--------------------------------------------------------------------------------------
#------------------------------------------------------  GET  --------------------------
@app.get("/api/Important_info", description=Important_Info, dependencies=[Depends(validate_accept)])
async def Info_requier(request: InformationModel):
    return load_Json(Files[request.info_request])
    

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
#------------------------------------------------------  Post --------------------------

