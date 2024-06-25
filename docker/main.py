import io
import os
import pickle
import shutil
import numpy as np
import uvicorn

from fastapi import FastAPI
from app.log import logger

app =FastAPI()
@app.get("/ping")
def ping():
    logger.info('Inside ping')
    
    return "pong"
@app.get("/predict_3")

def deploy_model_predict(modelId,datos):

    logger.info('Predicción del modelo modelId: ' + modelId)
    logger.info('Predicción del modelo con datos: ' + datos)
    #print(os.listdir())

    # Carga el modelo utilizando pickle u otra biblioteca adecuada
    modelpath = './model/' + modelId +'/model.pkl'
    logger.info('Load model from: '+modelpath)
    with open(modelpath, 'rb') as archivo:

        model = pickle.load(archivo)
    
    if (model is None):
        return ('No model found')

    trans_data = np.array([*eval(datos).values()]).reshape(1,-1)
    pred_model = model.predict(trans_data)[0]

    #logger.info('Predicción del modelo: '+ pred_model)

    return(pred_model)  
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7040)
