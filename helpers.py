import datetime
import html
import re
import time
import shortuuid



# Generates a UUID, which is used as an ID
def generateID():
    return shortuuid.uuid()


# Sanitizes the string to avoid XSS vulnerabilities
# Also removes any double spaces in between the strings
def sanitizeString(inputString):
    santizedString = html.escape(inputString, quote=False)
    santizedString = re.sub(' +', ' ', santizedString)
    return santizedString


# Checks if the date format is in DD-MMM-YYYY format, e.g. 23-May-2053
# Returns TRUE if its in the format or FALSE if its not
def checkDateFormat(inputDate):
    try:
        datetime.datetime.strptime(inputDate, "%d-%b-%Y")
        return True
    except:
        return False
    

# Converts date in DD-MMM-YYYY format, e.g. 23-May-2053 to Epoch
def convertDateToEpoch(inputDate):
    dateObject = datetime.datetime.strptime(inputDate, "%d-%b-%Y")
    epochTimestamp = int(dateObject.timestamp())
    return epochTimestamp


# Converts date in Epoch format to DD-MMM-YYYY format, e.g. 23-May-2053
def convertEpochToDate(inputDate):
    dateObject = datetime.datetime.fromtimestamp(inputDate)
    formattedDate = dateObject.strftime('%d-%b-%Y')
    return formattedDate