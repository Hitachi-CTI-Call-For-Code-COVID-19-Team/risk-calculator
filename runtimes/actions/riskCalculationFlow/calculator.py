# /*
# Copyright 2020 Hitachi Ltd.
 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
 
#  http://www.apache.org/licenses/LICENSE-2.0
 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# */

#### RISK CALULATOR FOR Store and Staff
#### Calculated risk is stored in  Risk Log DB
#### Parts: StoreRisk Calulation
#           Staff Risk Calculation 
#           Cumulative risk over the time
#           Treshold severty identification
#           Risk types identification

import json
from datetime import datetime
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey
from cloudant import cloudant
import pandas as pd
import numpy as np

def main(dict):

    processedData = dict["dataPeriodic"]
    riskOutputList = []
    riskStaffList = []
    data = json.loads(processedData)
    datalist = list(data.keys())
    # print(type(datalist))
    # rOutput = predefinedSettings("output_format", "")
    # riskOutputData = dict.fromkeys(datalist, rOutput)

    for each in datalist:

        identifier = each

    #     payload = newSensorData[identifier]["data"]["payload"]
        payload = data[identifier]["payload"]
        threshold = predefinedSettings(identifier,"threshold")
        weight = predefinedSettings(identifier,"weight")

        riskValue, severityValue = comparePayloadWithThreshold(payload, threshold)

        rType00 = predefinedSettings(identifier,"type")
        thisRiskOutput = setOutput(identifier, riskValue,severityValue, rType00)
        riskOutputList.append(thisRiskOutput)
        
        relatedStaffRisk = asessStaffRisk(thisRiskOutput)
#         print(relatedStaffRisk)
        if relatedStaffRisk is not None:
            riskStaffList.append(relatedStaffRisk)#json.loads(relatedStaffRisk))

    dataTowardsRiskLogDB = []
    if riskStaffList is not []:
        dataTowardsRiskLogDB = riskOutputList + riskStaffList
    # getRisk_condition()

    return {"calulatedRisks":json.dumps(dataTowardsRiskLogDB)}


#check belongs value for all belonging staff related to specific area
def asessStaffRisk(rOutput, assetData_Staff = [], staffIdentifier = "id", findingCriteria = "belongs"):
#     staffIdentifier = "id"
#     findingCriteria = "belongs"
    relevantStaff = ""
    c_staffRiskData = 0
    identifierArea = rOutput["id"]
    
    username_cloudant = "3c30e71f-1f5a-4498-af74-06860a23e042-bluemix"
    apikey_cloudant = "t7Lf7KxBAiqFOq6T_EW1dCQC1l1bZCP98q1YnBHxJUn4"
    client = Cloudant.iam(username_cloudant, apikey_cloudant)
    client.connect()
    assetData_Staff = client["assets_staff"]   
    
    workTime = 0
    last_restTime = 0
    timeslotDuration = 1
    
    staffFound = False
    
    for each in assetData_Staff:
        if (each[findingCriteria] == identifierArea):
            relevantStaff = each[staffIdentifier]
            
#             print(each["duration"]["slot"])
            start_time = datetime.strptime(each["duration"]["slot"]["start"], '%H:%M:%S')
            end_time = datetime.strptime(each["duration"]["slot"]["end"], '%H:%M:%S')
            
            timeslotDuration = end_time - start_time
            workTime = each["duration"]["on_job"]
            last_restTime = each["duration"]["last_rest"]
            print(workTime,last_restTime)

            staffFound = True
            
            break
    
    
    if staffFound is False:
        return None
            
    safetime = 30
    rType = ""
    

    work_Load = (workTime-last_restTime)/(timeslotDuration.total_seconds()/60)
#     print(workTime,last_restTime,timeslotDuration,(timeslotDuration.total_seconds()/60), work_Load)

        
    if work_Load >= 1:
        rType = rType +"_L"       # loaded
    if work_Load <= 0:
        rType = rType +"_R"       # LACK OF REST
    if last_restTime > safetime:
        rType = rType +"_W"       # havent washed
        
    c_staffRiskData = rOutput["risk"]["value"]* work_Load

    c_riskOutput, c_severity = comparePayloadWithThreshold(c_staffRiskData, relevantStaff) #, findingCriteria)
                           
    returnStaffRiskValue = setOutput(relevantStaff, c_riskOutput,c_severity, "st")
                           
    return returnStaffRiskValue
            
                           
def comparePayloadWithThreshold(payload0, id0):

    threshold0 = predefinedSettings(id0,"threshold")
    weight0 = predefinedSettings(id0,"weight")

#     print(threshold0)
    
    if("count" in str(payload0)):
        payload_value = payload0["count"]
    elif("amount_rate" in str(payload0)):
        payload_value = payload0["amount_rate"]
    else:
        payload_value = payload0

    lessTime = True  # time parameter that decides severity over time period

    threshold_veryHigh = threshold0[4]
    threshold_high = threshold0[3]
    threshold_medium = threshold0[2]
    threshold_low = threshold0[1]

    # Check for people congestion in count/second
    # ["data"]["payload"]["count"]#*1000/newSensorData0["data"]["payload"]["period"]
    o5 = payload_value >= threshold_veryHigh
    o4 = (payload_value >= threshold_high) and (
        payload_value < threshold_veryHigh)
    o3 = (payload_value >= threshold_medium) and (
        payload_value < threshold_high)
    o2 = (payload_value >= threshold_low) and (
        payload_value < threshold_medium)

    l = 5
    output0 = (o5*l + o4*(l-1) + o3*(l-3) + o2*(l-4)) / l*weight0  # ----> weights to be added here

    # setting range of severity
    if(o5 or o4):
        severityValue0 = "high"
    elif(o3 and lessTime):
        severityValue0 = "acceptable"
    else:
        severityValue0 = "low"

    return output0, severityValue0


def setOutput(identifier00, riskCurrent00, severityValue00, rType00):
                           
        cum_riskVal00 = riskCurrent00 #+ getCumulativeRiskValue(identifier00)
        # riskFormat = {
        #         "timestamp": "2020-07-07T00:07:33.307Z",  # current time stamp
        #         "id": "",
        #         "risk": {
        #             "value": 0,
        #             "cumValue": 0,
        #             "level": "",
        #             "type": ""
        #         }
        thisRiskOutput00 = {
        "timestamp": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),  # current time stamp
        "id": identifier00,
        "risk": {
            "value": riskCurrent00,
            "cumValue": cum_riskVal00,
             "level": severityValue00,
             "type":  predefinedSettings(identifier00,"type")#rType00
        }
        }

        return thisRiskOutput00


def getCumulativeRiskValue(identifier0):

    lastCumVal = 0.0
    username_cloudant = "3c30e71f-1f5a-4498-af74-06860a23e042-bluemix"
    apikey_cloudant = "t7Lf7KxBAiqFOq6T_EW1dCQC1l1bZCP98q1YnBHxJUn4"
    client = Cloudant.iam(username_cloudant, apikey_cloudant)
    client.connect()

    my_database = client["log_risk_calculation"]
    # docs = my_database.get_query_result(query0)

    test = my_database.get_query_result(selector={"timestamp": {"$exists": True},"id": {"$eq": identifier0}}, sort=[{"timestamp": "desc"}], limit=1)
    lastData = test.all()[0]
    if lastData is []:
        lastCumVal = 0.0
    else:
        lastCumVal = lastData["risk"]["cumValue"]

    return lastCumVal


def typeProof(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()


def predefinedSettings(object0, subObject0):
    
    staffAsset = {}
    # riskTypeSetting = {"overallR": 't', "staffR": "s", "congestionR": "c", "sanitisationR": "s", "disinfection": "d"}

    settingAssets = {
            'default': {'threshold': [5, 10, 20, 30, 40], 'weight': 1 , 'type': "d"},
            'staff': {'threshold': [0, .25, .5, .75, .1], 'weight': 1, 'type': "st"},
            'st00': {'threshold': [0, .25, .5, .75, .1], 'weight': 1, 'type': "st"},
            'congestion': {'threshold': [5, 10, 20, 30, 40], 'weight': 1, 'type': "c"},
            'sanitization': {'threshold': [5, 10, 20, 30, 40], 'weight': 1, 'type': "s"},
            'disinfection': {'threshold': [5, 10, 20, 30, 40], 'weight': 1, 'type': "d"},
            'handwash': {'threshold': [5, 10, 20, 30, 40], 'weight': 1, 'type': "s"},
            'toilet': {'threshold': [5, 10, 20, 30, 40], 'weight': 1, 'type': "d"},
            'garbage': {'threshold': [5, 10, 20, 30, 40], 'weight': 1, 'type': "d"},
            'overall': {'threshold': [5, 10, 20, 30, 40], 'weight': 1, 'type': "t"},
        }        
    
    for each in list(settingAssets.keys()):
#         print(each,object0)
        if each in object0:
            return settingAssets[each][subObject0]

    return settingAssets["default"][subObject0]


    #TBA
def thresholdDefinitons():
    pass
#TBA
def initialise_preSetData(idList):
    pass
