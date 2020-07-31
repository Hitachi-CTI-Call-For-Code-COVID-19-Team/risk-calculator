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

#
#
# main() will be run when you invoke this action
#
# @param Cloud Functions actions accept a single parameter, which must be a JSON object.
#
# @return The output of this action, which must be a JSON object.
#
#

# prepareData

# Prepare/Clean cloudant data for calculations
# Goal: Read Data
# 1. Read data periodically form sensor database --> dictionary
# 2. Read (sensor) asset dB and arrange (above) periodic data in dictionary format --->
# 3. Read (staff) asset DB to get attributes of each staff ---> list()


from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey
from cloudant import cloudant
import json
import pandas as pd
from datetime import datetime
import datetime
import numpy as np


def main(dict):

    period = 60
    rawData = dict["docs"]             # this is a list

    TypeCode = 'subType'                # asset DB: subtype
    IdCode = 'id'                       # asset DB: ID

    list_SensorTypes = getListedData(rawData)  # "parameter is json"
    allDataInterval = organiseInervalData(rawData, list_SensorTypes)
    dataPeriodic = normaliseIntervalData(allDataInterval)

    return {"dataPeriodic": dataPeriodic}


def getListedData(data0):

    list_ids = []
    list_subTypes = []

    for each in data0:
        identifier_each = each.get("deviceId", "")
        if identifier_each != "":
            list_ids.append(identifier_each)
            list_subTypes.append(each["deviceType"])

    deviceIdAndTypeLists = {
        "id": list(set(list_ids)),
        "subType": list(set(list_subTypes))
    }
    return deviceIdAndTypeLists


def organiseInervalData(data00, idList):

    ID_List = idList["id"]

    value = []

    dataMin = {}  # dict.fromkeys(ID_List,None)
    # print(dataMin)
    outL = []

    for i, each in enumerate(data00):

        each_data = each.get("data", "")

        if each_data != "":
            targetValue = ["area", "count"]
            if "area" in each["data"]["payload"]:
                targetValue = ["area", "count"]
            if "handwashStand" in each["data"]["payload"]:
                targetValue = ["handwashStand", "count"]
            if "garbageBin" in each["data"]["payload"]:
                targetValue = ["garbageBin", "amount_rate"]

            identifier = each["data"]["payload"][targetValue[0]]
            if identifier in dataMin:

                value = dataMin[identifier]['payload'][targetValue[1]]
                newValue = each['data']['payload'][targetValue[1]]

                if(type(value) is type([1, 2])):
                    outL = value + [newValue]
                else:
                    outL = [value] + [newValue]
            else:
                dataMin[identifier] = {}
                dataMin[identifier]['payload'] = each['data']['payload']
                outL = [each['data']['payload'][targetValue[1]]]

            dataMin[identifier]['payload'][targetValue[1]] = outL

    dataMin_json = json.dumps(dataMin)

    return dataMin_json


def normaliseIntervalData(dataMin_j):

    dataPerMinute = json.loads(dataMin_j)
    targetValue = "count"

    for identObject in dataPerMinute:
        if dataPerMinute[identObject] is not None:
            # print(identObject)
            dfCount = 0
            dfPayload = pd.DataFrame(dataPerMinute[identObject]['payload'])

            if ("area" in dataPerMinute[identObject]["payload"]) or ("handwashStand" in dataPerMinute[identObject]["payload"]):
                targetValue = "count"
                df_out = (dfPayload[targetValue].sum())

            if "garbageBin" in dataPerMinute[identObject]["payload"]:
                targetValue = "amount_rate"
                df_out = (dfPayload[targetValue]).iloc[-1]

    # #         dfCount_mean = dfPayload[targetValue].mean()
    # #         dfCount_min = dfPayload[targetValue].min()
    # #         dfCount_max = dfPayload[targetValue].max()
    # #         dfCount_median = dfPayload[targetValue].median()

            dataPerMinute[identObject]['payload'][targetValue] = typeProof(
                df_out)

    return dataPerMinute  # json.dumps(dataPerMinute)


def typeProof(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, datetime.datetime):
        return obj.__str__()
    else:
        return json.dumps(obj)
