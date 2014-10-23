"""
Copyright (c) 2014 Sandia Corporation. 
Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation, 
the U.S. Government retains certain rights in this software.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import api
import math
import random
import copy
import feClassUtils
import featureExtraction


import api, local_datastore, sys, getopt, re, os, logging, random, math, copy
import feClUtils

from operator import attrgetter
from collections import defaultdict

name = "kmeans"
logger = logging.getLogger(name)

def kmeansModel(args, opts):
    """ Plugin: kmeansModel
    Syntax: &<collection1> ... &<collectionN> | kmeansModel 
            --feature=<feature_name>       - e.g., --feature=byte_histogram (OPTIONAL)
            --k                    - The number of clusters to use
            --dontSave             - Does not save results to local datastore
            --rerun                - Reruns process even if stored results exist
            --noFeatureExtraction  - Do not perform feature extraction        
    """
    opts.update({'task':'cl', 'modeling':True, 'functionName':'kmeansModel'}) 
    if feClUtils.loadingFromLabel(opts):
        return feClUtils.getResultsUsingLabel(opts)
    feClUtils.addPreviousResultsDict(args,opts,featureExtraction.extractFeatures)
    opts['defaultNecessaryParameters'] = {'feature':'byte_histogram','normalize':True,'k':2,'distance':'euclidean'}
    if feClUtils.usingStoredResults(args,opts):
        return feClUtils.getStoredResults(opts)
        
    opts['labeledOIDs'],opts['centers'] = getKmeansModel(opts)
    
    feClUtils.addResultsDict(opts,['labeledOIDs','k','centers','distance','normalize'])
    opts['resultsDict']['classificationRating'] = rateClassification(args, opts)
    return opts['resultsDict']
    
    
def kmeansClassification(args, opts):
    """ Plugin: kmeansClassification
        Syntax: &<collection1> ... &<collectionN> | kmeansClassification 
                --feature=<feature_name>       - e.g., --feature=byte_histogram (OPTIONAL)
                --k                    - The number of clusters
                --dontSave             - Does not save results to local datastore
                --rerun                - Reruns process even if stored results exist
                --noFeatureExtraction  - Do not perform feature extraction     
    """
    opts.update({'task':'cl', 'modeling':False, 'functionName':'kmeansClassification'}) 
    if feClUtils.loadingFromLabel(opts):
        return feClUtils.getResultsUsingLabel(opts)

    opts['clModelDict'] = feClUtils.getStoredResults(opts)

    if feClUtils.usingStoredResults(args,opts):
        return feClUtils.getStoredResults(opts)

    if feClUtils.usingInputOIDs(opts):
        opts['oidData'] = feClUtils.getOIDData()
        opts['labeledOIDs'] = labelOIDs(opts)
    else:
        opts['labeledOIDs'] = opts['clModelDict']['labeledOIDs']
            
    feClUtils.addResultsDict(opts)
    return opts['resultsDict']
    
    
############### UTILITIES ######################################################
    
def rateClassification(args,opts):
    """
    Rates the classification of this clustering model using the Davies-Bouldin index
    see http://en.wikipedia.org/wiki/Davies%E2%80%93Bouldin_index for details
    """
    scatter = {}
    goodness = {}
    for centerId,centerData in opts['centers'].iteritems():
        #calculates scatter of each center which is just the sqrt of the average 
        #sqared Euclidean distance away of each point belonging to this cluster
        if len(opts['centers'][centerId]['oids']):
            scatter[centerId] = math.sqrt(sum([getEuclideanDistance(opts['oidData'][oid], centerData['values'])**2 for oid in opts['centers'][centerId]['oids']])/len(opts['centers'][centerId]['oids']))
        else:
            scatter[centerId] = 0

    for centerId in scatter.keys():
        #calculates "goodness" which is the max of each clusters scatter + another cluster divided by 
        #the distance between the clusters
        goodness[centerId] = max([(scatter[centerId]+scatter[center])/getEuclideanDistanceOfCenters(opts['centers'][centerId]['values'], opts['centers'][center]['values']) for center in scatter.keys() if center != centerId])

    #multiply by -1 because lower is better and all optimizations rely on larger values being better
    return -1 * sum(goodness.values()) / len(goodness.values())

def getKmeansModel(opts):
    oidDataRanges = getOIDDataRanges(opts)
    centers = getInitialCenters(opts)#, oidDataRanges)
    while assignmentsChanged(opts,centers):
        updateCenters(opts,centers)
    return getLabeledOIDs(centers), centers

def getDistance(oidData, centerValues, opts):
    if opts['distance'].lower() == 'euclidean':
        return getEuclideanDistance(oidData, centerValues)
    return getEuclideanDistance(oidData, centerValues)

def getEuclideanDistanceOfCenters(center1, center2):
    return getEuclideanDistance(dict([[valueKey,center1[valueKey]['value']] for valueKey in center1.keys()]), center2)

def getEuclideanDistance(oidData, centerValues):
    commonValueKeys = [valueKey for valueKey in oidData.keys() if valueKey in centerValues]
    return math.sqrt(sum([abs(oidData[valueKey] - centerValues[valueKey]['value'])**2 for valueKey in commonValueKeys]))

def labelOIDs(opts):
    labeledOIDs = {}
    for oid,oidData in opts['oidData'].iteritems():
        distance = sys.maxint
        closestCenter = None
        for centerID,centerData in opts['clModelDict']['centers'].iteritems():
            newDistance = getDistance(oidData,centerData['values'],opts)
            if newDistance < distance:
                distance = newDistance
                closestCenter = centerID
        labeledOIDs[oid] = closestCenter
    return labeledOIDs

def getLabeledOIDs(centers):
    labeledOIDs = {}
    for centerData in centers.values():
        for oid in centerData['oids']:
            labeledOIDs[oid] = centerData['id']
    return labeledOIDs
        
def updateCenters(opts,centers):
    for centerID,centerData in centers.iteritems():
        centers[centerID]['values'].clear()
        for oid in centerData['oids']:
            for oidDatumKey,oidDatum in opts['oidData'][oid]:
                if oidDatumKey not in centerData:
                    centers[centerID][oidDatumKey] = [oidDatum]
                else:
                    centers[centerID][oidDatumKey].append(oidDatum)
        for valueID,values in centers[centerID].keys():
            centerValues[valueID] = getAverage(values)
            
def getAverage(values):
    if len(values) == 0:
        return 0
    return float(sum(values)) / float(len(values))
        
def assignmentsChanged(opts,centers):
    oldCenterOIDs = dict((centerID,copy.copy(centerData['oids'])) for centerID,centerData in centers.iteritems())
    for centerID in centers.keys():
        del centers[centerID]['oids'][:]
    for oid,oidData in opts['oidData'].iteritems():
        distance = sys.maxint
        closestCenterID = None
        for centerID,centerData in centers.iteritems():
            newDistance = getDistance(oidData,centerData['values'],opts)
            if newDistance < distance:
                distance = newDistance
                closestCenterID = centerID
        centers[closestCenterID]['oids'].append(oid)
    for centerID,centerData in centers.iteritems():
        if len(centerData['oids']) != len(oldCenterOIDs[centerID]):
            return True
        for oid in centerData['oids']:
            if oid not in oldCenterOIDs[centerID]:
                return True
    return False
                    
def getInitialCenters(opts):
    oidDataRanges = getOIDDataRanges(opts)
    initialCenters = dict((str(k),getInitialCenter(opts,oidDataRanges,k)) for k in xrange(opts['k']))
    #assignmentsChanged = assignOIDsToCenters(opts,initialCenters)
    a = assignmentsChanged(opts,initialCenters)
    return initialCenters
    
def getInitialCenter(opts, oidDataRanges, centerID):
    return {'id':centerID,'oids':[],'values':dict((oidDatumKey,{'value':random.random()*(oidDatumRange['max']-oidDatumRange['min'])+oidDatumRange['min']}) for oidDatumKey,oidDatumRange in oidDataRanges.iteritems())}
    
def getOIDDataRanges(opts):
    oidDataRanges = {}
    for oidData in opts['oidData'].values():
        for oidDatumKey,oidDatum in oidData.iteritems():
            if oidDatumKey not in oidDataRanges:
                oidDataRanges[oidDatumKey] = {'min':oidDatum, 'max':oidDatum}
            elif oidDatum < oidDataRanges[oidDatumKey]['min']:
                oidDataRanges[oidDatumKey]['min'] = oidDatum
            elif oidDatum > oidDataRanges[oidDatumKey]['max']:
                oidDataRanges[oidDatumKey]['max'] = oidDatum
    return oidDataRanges

exports = [kmeansModel, kmeansClassification]

####################### OLD ##########################

def labelOIDs_OLD(opts):
    oids = opts['oids']
    k = opts['k']
    distance = opts['distance']
    clusterdata = {}
    oid_list = []
    
    for o in oids:
        clusterdata[o] = opts['oidData'][o]
        oid_list.append(o)
        
    km = key_map(clusterdata)
    data = [[0.0 for col in km] for row in clusterdata]
    for i, o in enumerate(oid_list):
        for key in clusterdata[o]:
            data[i][km[key]] = clusterdata[o][key]
            
    labels, centers = initialize(data, k)
    
    oid_list = opts['oids']
    
    for i, d in enumerate(data):
        label = -1
        mindist = 0.0
        for j in xrange(k):
            dist = distance_funcs[distance](d, centers[j])
            if label == -1 or dist < mindist:
                label = j
                mindist = dist
        labels[i] = label
    return dict((oid,label) for oid,label in zip(oid_list, labels))    
    
def print_results(args, opts):
    labels = set()
    for a in args:
        labels.add(a[1])
    for l in labels:
        print "Cluster %d:"%l
        for a in args:
            if a[1] == l:
                print a[0], api.get_names_from_oid(a[0]).pop()


def getKmeansModel_OLD(opts):
    oids = opts['oids']
    k = opts['k']
    distance = opts['distance']
    
    clusterdata = {}
    oid_list = []
    
    for o in oids:
    #    o_res = api.retrieve(module, o)
    #    if o_res:
        clusterdata[o] = opts['oidData'][o]
        oid_list.append(o)
    #if normalize:
    #    normalize_data(clusterdata)
        
    #flatten data
    km = key_map(clusterdata)
    data = [[0.0 for col in km] for row in clusterdata]
    for i, o in enumerate(oid_list):
        for key in clusterdata[o]:
            data[i][km[key]] = clusterdata[o][key]
            
    labels, centers = initialize(data, k)
    changed = True
    
    #Iterate
    while changed:
        changed = False

        #recalculate means
        empty, centers = getmeans(data, labels, centers)
        if empty:
            reassign(centers, labels, empty, k)
            empty, centers = getmeans(data, labels, centers)
            changed = True
        
        #reassign labels
        for i, d in enumerate(data):
            label = -1
            mindist = 0.0
            for j in xrange(k):
                dist = distance_funcs[distance](d, centers[j])
                if label == -1 or dist < mindist:
                    label = j
                    mindist = dist
            if label != labels[i]:
                labels[i] = label
                changed = True
    return dict((oid,label) for oid,label in zip(oid_list, labels)),centers
    #return zip(oid_list, labels)
    
def initialize(data, k):
    labels = [random.randint(0, k-1) for d in data]
    labels[0:k] = [i for i in xrange(k)]
    random.shuffle(labels)
    means = [[0.0 for col in data[0]] for row in xrange(k)]
    empty = getmeans(data, labels, means)
    return labels, means

def reassign(centers, labels, empty, k):
    for empty_label in empty:
        counts = [0 for col in xrange(k)]
        bisectable = set()
        for l in labels:
            counts[l] += 1
        bisectable = set( [ l for l in labels if counts[l] > 1 ] )        
        bisect = random.sample(bisectable, 1)[0]
        switch = [col for col in xrange(counts[bisect])]
        random.shuffle(switch)
        switch = switch[0:(counts[bisect]/2)]
        
        index = 0
        for i in xrange(len(labels)):
            if labels[i] == bisect:
                if index in switch:
                    labels[i] = empty_label
                index += 1


def getmeans(data, labels, means):
    count = [ 0 for c in means ]
    means = [ [ 0.0 for i in data[0] ] for c in means ]
    for l in labels:
        count[l] += 1
    for i, d in enumerate(data):
        for j, v in enumerate(d):
            means[labels[i]][j] += v
    means = [ [ j / float(c) for j in means[i] ] 
                if c else None for i, c in enumerate(count) ]
    empty = [ i for i in xrange(len(count)) if not count[i] ]
    return empty, means

def key_map(data):
    keys = set()
    for key in data:
        keys.update(data[key].keys())
    index = 0
    km = {}
    for index, i in enumerate(keys):
        km[i] = index
    return km

def normalize_data(data):
    for k in data:
        vals = data[k].values()
        n = snorm(vals)
        if n:
            for j in data[k]:
                data[k][j] /= n

def cosine(v1, v2):
    cos = dot(v1, v2) / (norm(v1) * norm(v2))

def euclidean(v1, v2):
    return norm(v1, v2)
    
def dot(v1, v2):
    return sum([ x*y for x, y in zip(v1, v2) ])

def snorm(v):
    return math.sqrt(sum([ x*x for x in v ]))

def norm(v1, v2):
    return math.sqrt(sum([ (x-y)*(x-y) for x, y in zip(v1, v2) ]))
    
distance_funcs = {"cosine":cosine, "euclidean":euclidean}
