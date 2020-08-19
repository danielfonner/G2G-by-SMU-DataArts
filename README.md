# G2G-by-SMU-DataArts
Extracting grant data from e-filed 990PFs and connecting grants to the nonprofits receiving the grants

Created by Daniel F. Fonner, Associate Director for Research, SMU DataArts (Southern Methodist University), dfonner@smu.edu, https://culturaldata.org/

In 2016, the IRS partnered with Amazon Web Services (AWS) to make all e-filed 990s available as XML documents on AWS (generally 2011 to present). This development allows for large-scale analysis of the full text of 990s as opposed to the limited extracts produced by the IRS annually. One important aspect of machine-readable 990s is that we can extract grant data from 990PFs, where grantmakers list who they granted money to, for what purpose, and what amount. <https://aws.amazon.com/blogs/publicsector/irs-990-filing-data-now-available-as-an-aws-public-data-set/>



(Side note on E-filed 990s: To date, most tax exempt organizations have not been required to e-file their 990s. With passage of the Taxpayers First Act in 2019, all tax-exempt entities will have to e-file their 990s for tax years beginning after July 1, 2019 with the exception of 990EZ filers who have an additonal year before the requirement must be met. I will note in the limitations below that the grant data extracted in this repository is limited to 990PF filers who have e-filed their 990s. Going forward, the grant data will be more complete as all tax exempt organizations are required to e-file. <https://www.irs.gov/newsroom/irs-recent-legislation-requires-tax-exempt-organizations-to-e-file-forms>)

You can read more about the AWS data here: https://docs.opendata.aws/irs-990/readme.html


The Python code in this repository creates a CSV file for all grants listed on e-filed 990PFs submitted in a given year. Note that the problem solved by this code is that 990PFs do not list the EIN of grantees, and this code identifies and appends the EIN and other data to the grant data. Each file in this repository was created using this code. The results are similar to data created by IBM Watson's Causebot a few years ago. <https://data.world/causebot/grant-2010-to-2016> Watson's method was not documented, so this Python code allows for the re-creation of that data as well as updating for future filings. Note that due to the number of filings and process of matching grants to grantees, this code takes a while to run on a standard computer. (Also note that this script is not the most "Pythonic", and as I continue to experiment, I will update and clean the code.)


WHAT THE PYTHON SCRIPT DOES GENERALLY:
  1) Download IRS Business Master File (BMF) and AWS Index Files
  2) Using the Index files, extract grant data from 990PFs part XV for both granted and approved for future grants
  3) Match grants to grantees using a string-matching method (fuzzywuzzy), also requiring matches to have the same zip code
  4) Append grantee EIN and NTEE data to each grant using the BMF
  5) Append grantor NTEE to each grant using the BMF

To learn more about the string-matching method, see: https://chairnerd.seatgeek.com/fuzzywuzzy-fuzzy-string-matching-in-python/ This code currently uses a score threshoold of 80 for matches.

LIMITATIONS OF THIS DATA/APPROACH:
  1) Only grant data available is from tax-exempt entities that have e-filed their 990PFs (grantee information from the BMF is for all tax-exempt entities)
  2) Requires standard reporting of e-filed 990PFS
    (a) Many organizations fill out Part XV as intended: see Ford Foundation 990PF here: https://projects.propublica.org/nonprofits/organizations/131684331/201803209349100025/full
    (b) However, some e-filed 990PFs attach a seperate schedule that is not readable via an XML document: see Geraldine R Dodge Foundation 990PF here: https://projects.propublica.org/nonprofits/organizations/237406010/201503199349100420/full
  3) Also regarding standard formatting, in the Ford Foundation exmaple above, you can look through their grants given and notice that some grants have $0 in the amount space with an actual dollar amount at the beginning of the grant description space. This code does not extract those dollar values from the grant description as the format could vary widely across grantmakers. Future work could attempt to better extract information.
  4) Some organizations are composed of more than one part, each having their own EIN associated with the same primary name and address. Since there is not an easy way to determine which EIN is correct, this code utilizes the first EIN as listed in the BMF. Future work could attempt to better select EINs for organizations composed of many parts. For example, see American Cancer Society in Atlanta, GA.
  5) Note that NTEE codes as shown in the BMF are assigned to grantmakers and grantees so may not be completely accurate. However, this work aligns with the BMF so if one has methods for reclassifying organizations, that could easily be applied to this data.


COLUMN DESCRIPTIONS FOR CSV FILES:
  1) grantorName - Name of grantor from 990PF XML
  2) grantorEIN - EIN of grantor from 990PF XML
  3) grantorNTEE - NTEE of grantor from BMF
  4) grantorTaxPeriodEnd - 990PF tax period end date of grantor from XML
  5) granteeName - Name of grantee from 990PF XML
  6) granteeEIN - EIN of grantee from BMF
  7) granteeNTEE - NTEE of grantee from BMF
  8) granteeCity - City of grantee from 990PF XML
  9) granteeState - State code of grantee from 990PF XML
  10) granteeZip - Zip code (5 characters) of grantee from 990PF XML
  11) granteeOrgType - Organization type of grantee from 990PF XML, such as PC for public charity. See 990PF instructions for more info: https://www.irs.gov/pub/irs-pdf/i990pf.pdf
  12) grantDescription - Description of grant from 990PF XML
  13) grantAmount - Dollar value of grant from 990PF XML
  14) paidOrFuture - Notes whether grant was paid or approved for future payment, from 990PF XML
  15) grantor_XML_URL - URL to the grantor's raw 990PF XML data for the year grant was noted
  16) grantor_formatted_990_URL - URL to the grantor's formatted 990PF for the year grant was noted, link to ProPublica's Nonprofit Explorer


NUMBER OF GRANTS FOUND IN EACH YEAR:
  1) 2015: COMING SOON!
  2) 2016: COMING SOON!
  3) 2017: COMING SOON!
  4) 2018: COMING SOON!
  5) 2019: COMING SOON!
  6) 2020: COMING SOON! (note this is as of MM/DD/YYYY)
  
  (Note that for submission years prior to 2014, the XML tags are a little different for 990PFs, requiring a slightly different script. Additionally, I'm trying to fix a strange bug with the 2014 AWS index file. I will create a new script for those older years soon.)
  
  ADD NOTE ON ACCURACY!
  
  Finally, we are currently working on developing a tool that will allow for easier exploration of this data rather than solely being in CSV format. More to come!
