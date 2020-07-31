#
#
# main() will be run when you invoke this action
#
# @param Cloud Functions actions accept a single parameter, which must be a JSON object.
#
# @return The output of this action, which must be a JSON object.
#
#
import sys
import json
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.query import Query
from cloudant import cloudant


def main(dict):

    username_cloudant = ""                      #   "INPUT YOUR CLOUDANT CREDENTIALS"
    apikey_cloudant =   ""                      #   "INPUT YOUR CLOUDANT CREDENTIALS"
    client = Cloudant.iam(username_cloudant, apikey_cloudant)
    client.connect()
    my_database = client["assets_staff"]

    listIdentifiers = list(dict["dataPeriodic"].keys())
    selector = {"belongs": {"$in": listIdentifiers}}

    query_result = my_database.get_query_result(selector)

    return {'relevantStaffData': query_result.all(),
            'dataPeriodic': dict["dataPeriodic"]
            }
