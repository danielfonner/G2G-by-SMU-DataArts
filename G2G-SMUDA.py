# G2G-SMUDA  - Grantor2Grantee - 1 year at a time


# Prepared by Daniel F. Fonner, Associate Director for Research, SMU DataArts -- dfonner@smu.edu


import argparse
import csv
import numpy as np
import pandas as pd
import os, sys
import statistics
import math
import requests
import xml.etree.ElementTree as ET
import recordlinkage
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import shutil
import glob
import urllib.request


############################################################################
## PART 1 - Download index and BMF files                                ####
############################################################################

print("Start part 1 - download index and bmf files")

# Save index files - Change year at end of URL for different indexes. 2014 is the earliest available with the XML tags used here.  Note that one could set up argparse to put the year as as input for running the script.
urllib.request.urlretrieve('https://s3.amazonaws.com/irs-form-990/index_2014.csv', 'index_data.csv')


# Save BMF files and combine into one csv.  Using this BMF means that orgs who are no longer listed in the BMF may not get matches to Index files in the past when they might have existed. One method would be to use BMF files from the National Center for Charitable statistics for older years.

urllib.request.urlretrieve('https://www.irs.gov/pub/irs-soi/eo1.csv', 'bmf1.csv')
urllib.request.urlretrieve('https://www.irs.gov/pub/irs-soi/eo2.csv', 'bmf2.csv')
urllib.request.urlretrieve('https://www.irs.gov/pub/irs-soi/eo3.csv', 'bmf3.csv')
urllib.request.urlretrieve('https://www.irs.gov/pub/irs-soi/eo4.csv', 'bmf4.csv')

bmf1 = pd.read_csv("bmf1.csv")
bmf2 = pd.read_csv("bmf2.csv")
bmf3 = pd.read_csv("bmf3.csv")
bmf4 = pd.read_csv("bmf4.csv")

listOfBMFFiles = [bmf1, bmf2, bmf3, bmf4]

dfCombinedCSV = pd.concat(listOfBMFFiles, axis=0, ignore_index=True)


# Save new dataframe to CSV
fileNameForCombinedCSV = "bmf.csv"
convertToCSV = dfCombinedCSV.to_csv(fileNameForCombinedCSV)


# To Clean up, delete component bmf files
os.remove("bmf1.csv")
os.remove("bmf2.csv")
os.remove("bmf3.csv")
os.remove("bmf4.csv")

print('Part 1 Complete')

############################################################################
## PART 2 - extract XML grant data from AWS                            ####
############################################################################

print("Start part 2 - extract XML grant data from AWS")

#######
#Import CSVs of index files for AWS data
# Note that this could be coded, once looking at all potential 990 data, to only pull data submitted since the last time this script was run.  That will allow for updating newly submitted data without needing to rerun on all 990 data every time. That would only be necessary for the current year's index file.

dfIndex = pd.read_csv("index_data.csv") 
dfIndex = dfIndex[dfIndex['RETURN_TYPE']=="990PF"]
dfIndex['URL_for_Data_Raw_XML'] = "https://s3.amazonaws.com/irs-form-990/" + dfIndex['OBJECT_ID'].astype(str) + "_public.xml"  # Creates url path to relevant XML document
dfIndex['URL_for_most_recent_990'] = "https://projects.propublica.org/nonprofits/organizations/" + dfIndex['EIN'].astype(str) + "/" + dfIndex['OBJECT_ID'].astype(str) + "/full"


#### Extract all grant data from 990PFs identifying them from AWS index file
##   Store as dataframe with columns in newColumns variable below
##   Create new df using the index file that extracts grantor/grantee data. Each row will be a unique grant
##   Needs to loop through all grants for a particular foundation - both paid and approved for future. Also include column for the xml document from which the grant comes from as well as formatted 990 on Propublica.

newColumns = ['grantorName', 'grantorEIN', 'grantorTaxPeriodEnd', 'granteeName','granteeCity', 'granteeState', 'granteeZip', 'granteeOrgType', 'grantDescription', 'grantAmount', 'paidOrFuture', 'grantor_XML_URL', 'grantor_formatted_990_Url']
dfGrants = pd.DataFrame(columns = newColumns)

# Setting up counter
numberOfRows = len(dfIndex.index)
count = 0

for rows in dfIndex['URL_for_Data_Raw_XML']:

    count += 1
    print(str(count) + "/" + str(numberOfRows) + " foundations that e-filed")

    # Get XML doc based on index file
    response = requests.get(rows)
    with open('orgXML.xml', 'wb') as f:
        f.write(response.content) 

    tree = ET.parse('orgXML.xml')
    root = tree.getroot()

    # Store grantor info as variables
    for grantor in root.findall('.//{http://www.irs.gov/efile}Filer'):
        grantorName = grantor.findtext('.//{http://www.irs.gov/efile}BusinessNameLine1Txt')
    
    grantorEIN = root.findtext('.//{http://www.irs.gov/efile}EIN')
    grantorTaxPeriodEnd = root.findtext('.//{http://www.irs.gov/efile}TaxPeriodEndDt')

    formatted_990_Url = dfIndex['URL_for_most_recent_990'].values[count-1]

    # loop through all grants per document to get grantee data - Grants Paid During Year
    for grantPaid in root.findall('.//{http://www.irs.gov/efile}GrantOrContributionPdDurYrGrp'):
        granteeName = grantPaid.findtext('.//{http://www.irs.gov/efile}BusinessNameLine1Txt')
        granteeCity = grantPaid.findtext('.//{http://www.irs.gov/efile}CityNm')
        granteeState = grantPaid.findtext('.//{http://www.irs.gov/efile}StateAbbreviationCd')
        granteeZip = str(grantPaid.findtext('.//{http://www.irs.gov/efile}ZIPCd'))[:5]
        granteeOrgType = grantPaid.findtext('.//{http://www.irs.gov/efile}RecipientFoundationStatusTxt')
        grantDescription = grantPaid.findtext('.//{http://www.irs.gov/efile}GrantOrContributionPurposeTxt')
        grantAmount = grantPaid.findtext('.//{http://www.irs.gov/efile}Amt')
        paidOrFuture = "Paid during year"

        #Add row in dfGrants for each grant
        currentRowCount = dfGrants.shape[0]
        currentRowCountPlusOne = currentRowCount + 1
        dfGrants.loc[currentRowCountPlusOne] = [grantorName, grantorEIN, grantorTaxPeriodEnd, granteeName, granteeCity, granteeState, granteeZip, granteeOrgType, grantDescription, grantAmount, paidOrFuture, rows, formatted_990_Url]



    # loop through all grants per document to get grantee data - Grant Approved for future payment
    for grantFuture in root.findall('.//{http://www.irs.gov/efile}GrantOrContriApprvForFutGrp'):
        granteeName = grantFuture.findtext('.//{http://www.irs.gov/efile}BusinessNameLine1Txt')
        granteeCity = grantFuture.findtext('.//{http://www.irs.gov/efile}CityNm')
        granteeState = grantFuture.findtext('.//{http://www.irs.gov/efile}StateAbbreviationCd')
        granteeZip = str(grantFuture.findtext('.//{http://www.irs.gov/efile}ZIPCd'))[:5]
        granteeOrgType = grantFuture.findtext('.//{http://www.irs.gov/efile}RecipientFoundationStatusTxt')
        grantDescription = grantFuture.findtext('.//{http://www.irs.gov/efile}GrantOrContributionPurposeTxt')
        grantAmount = grantFuture.findtext('.//{http://www.irs.gov/efile}Amt')
        paidOrFuture = "Approved for future  payment"

        #Add row in dfGrants for each grant
        currentRowCount = dfGrants.shape[0]
        currentRowCountPlusOne = currentRowCount + 1
        dfGrants.loc[currentRowCountPlusOne] = [grantorName, grantorEIN, grantorTaxPeriodEnd, granteeName, granteeCity, granteeState, granteeZip, granteeOrgType, grantDescription, grantAmount, paidOrFuture, rows, formatted_990_Url]


    


# Remove the XML document from the directory
os.remove('orgXML.xml')


# Clean up zips that are null
conditions = [(dfGrants['granteeZip'] != "None"), (dfGrants['granteeZip'] == "None")]
choices = [(dfGrants['granteeZip']),(np.NaN)]

dfGrants['granteeZip'] = np.select(conditions, choices)

# Save new dataframe to CSV
dfGrants.index.name = 'indexExtract'

fileNameForNewDF = "g2g_XML_extract_pre_merge.csv"
convertToCSV2 = dfGrants.to_csv(fileNameForNewDF)

# To clean up the directory in production, remove the Index file that was downloaded at the start of this script.
os.remove("index_data.csv")



print('Part 2 Complete')

############################################################################
## PART 3 - fuzzy merge on organization name to get grantee EIN and NTEE####
############################################################################

print("Start part 3 - fuzzy merge on organization name to get grantee EIN and NTEE")

#######
# Make directory for saving CSVs of merged by zip from loop below

directory = os.getcwd()
csvs = "merged_csvs_by_zip_grantees"
pathCSVs = directory + "/" + csvs
if os.path.exists(pathCSVs):
    shutil.rmtree(pathCSVs)
os.mkdir(pathCSVs)


#Import CSVs of extract file from other G2G script and BMF

dfG2GExtractAll = pd.read_csv("g2g_XML_extract_pre_merge.csv")
dfG2GExtract = dfG2GExtractAll[dfG2GExtractAll['granteeState'].notnull()]

dfBMF = pd.read_csv("bmf.csv") 
dfBMF = dfBMF[['EIN','NAME','ZIP','NTEE_CD']]
dfBMF = dfBMF.rename(columns={'EIN':'granteeEIN', 'NAME':'granteeBMFName','ZIP':'granteeBMFZip','NTEE_CD':'granteeNTEE'})

dfBMF['granteeBMFZip'] = dfBMF['granteeBMFZip'].str.slice(0,5)
dfBMF['granteeBMFZip'] = pd.to_numeric(dfBMF['granteeBMFZip'], errors='coerce')


# Get unique values from dfG2GExtract granteeZip to allow for minimizing size of BMF for counter in loop
zipListFromdfG2GExtract = dfG2GExtract.granteeZip.unique().tolist()
numberOfZips = len(zipListFromdfG2GExtract)
count = 0


# Define function for fuzzy merge - Idea for function found here: https://stackoverflow.com/questions/13636848/is-it-possible-to-do-fuzzy-match-merge-with-python-pandas

def fuzzy_merge(df_1, df_2, key1, key2, threshold=80, limit=1):
    """
    :param df_1: the left table to join
    :param df_2: the right table to join
    :param key1: key column of the left table
    :param key2: key column of the right table
    :param threshold: how close the matches should be to return a match, based on Levenshtein distance
    :param limit: the amount of matches that will get returned, these are sorted high to low
    :return: dataframe with boths keys and matches
    """
    s = df_2[key2].tolist()

    m = df_1[key1].apply(lambda x: process.extract(x, s, limit=limit))    
    df_1['matches'] = m

    m2 = df_1['matches'].apply(lambda x: ', '.join([i[0] for i in x if i[1] >= threshold]))
    df_1['matches'] = m2

    return df_1


# For loop to look join Extract and BMF using fuzzywuzzy by limiting to zip codes for each loop
for zips in zipListFromdfG2GExtract:
    count += 1
    print(str(count) + "/" + str(numberOfZips) + "zip codes")

    # Only look at one set of zips for BMF and Extract for each loop
    dfBMFLoop = dfBMF[dfBMF['granteeBMFZip']==zips]
    dfG2GExtractLoop = dfG2GExtract[dfG2GExtract['granteeZip']==zips]

    # Identify if there are any matches
    dfFuzzyMatchLoop = fuzzy_merge(dfG2GExtractLoop, dfBMFLoop, 'granteeName', 'granteeBMFName')

    # Join based on matches
    dfMergedGrantWGrantee = pd.merge(dfFuzzyMatchLoop, dfBMFLoop, how='left', left_on=['matches'], right_on=['granteeBMFName'])

    # Delete "matches" column and delete granteeBMFZip and granteeBMFName
    del dfMergedGrantWGrantee['matches']
    del dfMergedGrantWGrantee['granteeBMFName']
    del dfMergedGrantWGrantee['granteeBMFZip']
    
    # Keep first EIN associated with name then delete indexExtract
    dfMergedGrantWGrantee.drop_duplicates(subset = "indexExtract", keep = "first", inplace = True)
    
    # Save each merged df
    pathToSaveCSVs = pathCSVs + "/" + "g2g_matching_" + str(zips) + ".csv"
    dfMergedGrantWGrantee.to_csv(pathToSaveCSVs)


# Combine the zip dataframes into one dataframe.  

all_files = glob.glob(pathCSVs + "/*.csv")
listOfFiles = []
for filename in all_files:
    df = pd.read_csv(filename, index_col=None, header=0)
    listOfFiles.append(df)

dfAllZipsMerged = pd.concat(listOfFiles, axis=0, ignore_index=True)

# Bring back grants with no zip
dfAllZipsAndNull = dfAllZipsMerged.append(dfG2GExtractAll, sort=False)
dfAllZipsAndNull.drop_duplicates(subset = "indexExtract", keep = "first", inplace = True)

# Convert granteeEIN and granteeNAICS to integers 
dfAllZipsAndNull['granteeEIN'] = dfAllZipsAndNull['granteeEIN'].astype('Int64')
del dfAllZipsAndNull['Unnamed: 0']
del dfAllZipsAndNull['indexExtract']


# Save new dataframe to CSV
fileNameForNewDF = "g2g_matching_grantees.csv"
convertToCSV2 = dfAllZipsAndNull.to_csv(fileNameForNewDF)


# To Clean up, delete folder "merged_csvs_by_zip_grantees" and pre-merge file "g2g_XML_extract_pre_merge.csv"
os.remove("g2g_XML_extract_pre_merge.csv")
shutil.rmtree("merged_csvs_by_zip_grantees")


print('Part 3 Complete')


############################################################################
## PART 4 - join to get grantor NTEE                                    ####
############################################################################

print("Start part 4 - join to get grantor NTEE")


#######

#Import CSVs of matched grants file from second G2G script and BMF

dfMatchedGrants = pd.read_csv("g2g_matching_grantees.csv")

dfBMF = pd.read_csv("bmf.csv")
dfBMF = dfBMF[['EIN','NTEE_CD']]
dfBMF = dfBMF.rename(columns={'EIN':'grantorEIN','NTEE_CD':'grantorNTEE'})

# Merge 
dfMergedGrantWGrantor = pd.merge(dfMatchedGrants, dfBMF, how='left', left_on=['grantorEIN'], right_on=['grantorEIN'])


# Rearrange Columns
dfMergedGrantWGrantor = dfMergedGrantWGrantor[['grantorName','grantorEIN','grantorNTEE','grantorTaxPeriodEnd','granteeName','granteeEIN','granteeNTEE','granteeCity','granteeState','granteeZip','granteeOrgType','grantDescription','grantAmount','paidOrFuture','grantor_XML_URL','grantor_formatted_990_Url']]

# Save new dataframe to CSV
fileNameForNewDF = "g2g_matching_grantors_final.csv"
convertToCSV2 = dfMergedGrantWGrantor.to_csv(fileNameForNewDF)

# To Clean up, delete file from second scrript "g2g_matching_grantees.csv" and delete BMF
os.remove("g2g_matching_grantees.csv")
os.remove("bmf.csv")



print('Part 4 Complete')

############################################################################
## PART 5 - count total rows/number of grants                           ####
############################################################################

print("Start part 5 - count total rows/number of grants  ")

print(len(dfMergedGrantWGrantor.index))

print('Part 5 Complete')
print('Script Complete')
