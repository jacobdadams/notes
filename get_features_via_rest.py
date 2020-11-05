'''
get_features_via_rest.py: downloads all the features from a feature service by calling the REST api and
converting the resulting JSON to a feature class. Originally written for 32-bit py 2.7; untested in py
64-bit py 3 but basics should work.

This was extracted from an old script and hasn't been tested on its own. Only intended to show the basic ideas.

Provided as-is, no warranties express or implied. 
'''

import arcpy
import json
import os
import copy
import tempfile
import datetime
import urllib

def get_json(request):

    #: Python 2 vs 3
    # url_object = urllib2.urlopen(request)
    url_object = urllib.request.urlopen(request)
    response = url_object.read()
    return json.loads(response)


def by_json(ids, base_URL, date, output_fc, batch_size):
    '''
    Gets features by loading everything into memory, then writing it all out
    to a JSON file, then using arcpy to load JSON into a feature class.
    2x faster than using feature sets, but uses lots of memory (tens of gb on
    the SL County Parcels feature set).
    '''
    # dictionary to hold JSON representation of all downloaded features
    features_json = {}
    total_count = len(ids)
    num_batches = -(-total_count // batch_size)  # ceiling dvision
    batch = 1
    for i in range(0, total_count, batch_size):
        # Using "where oid >= x and oid <= y" (get all features between x and y
        # inclusive), set x to be oid[i], y to be oid[i + (batch_size-1)] to
        # make sure we don't get any duplicates
        i_plus = i+batch_size-1  # batch end index
        if i_plus < total_count:  # boundary check on last batch's end index
            begin_oid = ids[i]
            end_oid = ids[i_plus]
        else:  # if last batch index goes out of bounds, just use last oid
            begin_oid = ids[i]
            end_oid = ids[-1]

        # Create querry, download features as json
        query = "query?where=OBJECTID%20%3E={}%20and%20OBJECTID%20%3C=%20{}&outFields=*&returnGeometry=true&f=json".format(begin_oid, end_oid)
        features_url = base_URL + query
        percent = float(batch - 1) / float(num_batches) * 100.0
        print("Downloading {} to {} ({} of {}, {:.1f}%)".format(begin_oid, end_oid, batch, num_batches, percent,))

        batch_json = get_json(features_url)

        # If the dictionary's structure already exists, just extend the features
        # list. Otherwise, deepcopy the downloaded dict to features_json.
        # We can do this because the other information about the feature set
        # is the same from batch to batch.
        if 'features' in features_json.keys():
            features_json['features'].extend(batch_json['features'])
        else:
            features_json = copy.deepcopy(batch_json)

        batch += 1

    # Write json out to text file then import it to feature class using arcpy
    print("Creating single JSON string...")
    json_fname = "json_{}.json".format(date)
    json_output = os.path.join(tempfile.gettempdir(), json_fname)
    json_string = json.dumps(features_json)
    del features_json  # Delete feature dictionary to save lots of memory
    print("Writing JSON to temp file...")
    with open(json_output, 'a') as jfile:
        jfile.write(json_string)
    del json_string  # Delete feature string to save lots of memory

    print("Converting JSON to feature class...")
    arcpy.JSONToFeatures_conversion(json_output, output_fc)

    # Clean up after ourselves
    os.remove(json_output)


def by_featureset(ids, base_URL, date, output_fc, batch_size):
    '''
    Gets features by loading each batch as a feature set, then copying the
    feature set into the feature class. Takes at least 2x longer than by_json
    but doesn't need lots of memory (will work in 32-bit python)
    '''
    total_count = len(ids)
    num_batches = -(-total_count // batch_size)  # ceiling dvision
    batch = 1
    for i in range(0, total_count, batch_size):
        # Using "where oid >= x and oid <= y" (get all features between x and y
        # inclusive), set x to be oid[i], y to be oid[i + (batch_size-1)] to
        # make sure we don't get any duplicates
        i_plus = i+batch_size-1  # batch end index
        if i_plus < total_count:  # boundary check on last batch's end index
            begin_oid = ids[i]
            end_oid = ids[i_plus]
        else:  # if last batch index goes out of bounds, just use last oid
            begin_oid = ids[i]
            end_oid = ids[-1]

        # Create querry, download features as json
        query = "query?where=OBJECTID%20%3E={}%20and%20OBJECTID%20%3C=%20{}&outFields=*&returnGeometry=true&f=json".format(begin_oid, end_oid)
        features_url = base_URL + query
        percent = float(batch - 1) / float(num_batches) * 100.0
        print("Downloading {} to {} ({} of {}, {:.1f}%)".format(begin_oid, end_oid, batch, num_batches, percent,))

        # load query into a feature set
        fs = arcpy.FeatureSet()
        fs.load(features_url)

        # Copy feature set into parcel feature class if it already exists,
        # append otherwise
        if arcpy.Exists(output_fc):
            arcpy.Append_management(fs, output_fc)
        else:
            arcpy.CopyFeatures_management(fs, output_fc)

        #print("Features in {}: {}").format(output_fc, arcpy.GetCount_management(output_fc))
        batch += 1

def main():

    #: Should point directly the desired layer within the feature service:
    #: https://services.arcgis.com/<id>/arcgis/rest/services/<service_name>/FeatureServer/0 
    #: for the first layer in <service_name>
    service_URL = ""

    output_feature_class = r''

    date = datetime.datetime.today()

    print("Downloading features...")
    # Get list of OID so we can query specific features (gets around maxRecordCount limitations)
    oids_url = service_URL + "query?where=1=1&returnIdsOnly=true&f=pjson"
    oids_json = get_json(oids_url)
    oids = oids_json['objectIds']
    #print("Number of OIDS: {}").format(len(oids))

    #: Get server's maxRecordCount, use as batch size so we can download everything by splitting it up
    #: into separate requests if necessary
    maxrec_url = service_URL + "?f=pjson"
    maxrec_json = get_json(maxrec_url)
    batch_size = maxrec_json["maxRecordCount"]
    print("Batch size: {}".format(batch_size))

    # Download the parcels into the working gdb
    # by_json(oids, service_URL, date, output_feature_class, batch_size)
    by_featureset(oids, service_URL, date, output_feature_class, batch_size)