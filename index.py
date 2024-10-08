import sqlite3
from fastapi import FastAPI, Response, status, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from helpers import *
from fastapi.templating import Jinja2Templates


app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/")
def landingPage():
    return FileResponse("AmountTracker.html")


# POST Body to add an amount
# The amount is validated to be greater than 0
class addAnAmount(BaseModel):
    amountDescription: str
    amount: float = Field(gt=0, description="Amount must be greater than 0")
    date: str

# Add an amount endpoint


@app.post("/addAnAmount")
def addAnAmount(addAnAmountBody: addAnAmount, response: Response):

    # Sanitzes the description
    # Checks if the date format is correct
    sanitizedDescription = sanitizeString(
        addAnAmountBody.amountDescription).strip()
    sanitizedDate = checkDateFormat(addAnAmountBody.date)

    # Checks the amount description, if its empty returns a 400
    if len(sanitizedDescription) == 0:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"status": "Amount description cannot be empty."}

    # Checks the date format, if its incorrect returns a 400
    if sanitizedDate == False:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"status": addAnAmountBody.date + " is not a valid date or is not in DD-MMM-YYYY format, e.g., 05-Aug-2024. Please correct the date."}

    # Connects to the DB
    connection = sqlite3.connect("AMOUNTTRACKER.db")
    cur = connection.cursor()

    # Inserts the amount into the DB and returns the generated ID in the response
    queryToAddAnAmount = "INSERT INTO AMOUNTTRACKER (ID, AMT_EXP_DESC, VALUE, TYPE, DATE) Values (?, ?, ?, ?, ?)"
    generatedIDForAmount = generateID()
    valuesToAddAnAmount = (generatedIDForAmount, sanitizedDescription,
                           addAnAmountBody.amount, 'AMT', convertDateToEpoch(addAnAmountBody.date))
    cur.execute(queryToAddAnAmount, valuesToAddAnAmount)
    connection.commit()
    return {"amountID": generatedIDForAmount, "status": "Amount of " + str(addAnAmountBody.amount) + " added."}


# POST Body to add an expense
# The expense is validated to be greater than 0
class addAnExpense(BaseModel):
    amountID: str
    expenseDescription: str
    expense: float = Field(gt=0, description="Expense must be greater than 0")
    date: str


# Add an expense endpoint
@app.post("/addAnExpense")
def addAnExpense(addAnExpenseBody: addAnExpense, response: Response):

    # Sanitzes the description
    # Checks if the date format is correct
    sanitizedDescription = sanitizeString(
        addAnExpenseBody.expenseDescription).strip()
    sanitizedDate = checkDateFormat(addAnExpenseBody.date)

    # Checks the expense description, if its empty returns a 400
    if len(sanitizedDescription) == 0:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"status": "Expense description cannot be empty."}

    # Checks the date format, if its incorrect returns a 400
    if sanitizedDate == False:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"status": addAnExpenseBody.date + " is not a valid date or is not in DD-MMM-YYYY format, e.g., 05-Aug-2024. Please correct the date."}

    # Connects to the DB
    connection = sqlite3.connect("AMOUNTTRACKER.db")
    cur = connection.cursor()

    # Checks if the supplied amount ID exists in the DB.
    # We try to fetch the ID, DATE and VALUE from the DB for that ID
    # If there is no amount ID by that ID, it will return NONE, we return with 404
    queryToCheckAmountID = "SELECT ID, DATE, VALUE FROM AMOUNTTRACKER WHERE ID = ? AND TYPE = 'AMT'"
    valuesToCheckAmountID = [addAnExpenseBody.amountID]
    amountIDCheck = cur.execute(
        queryToCheckAmountID, valuesToCheckAmountID).fetchone()
    if amountIDCheck is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"status": "No Amount with the ID " + addAnExpenseBody.amountID + " exists. Please recheck"}

    # Checking if the date of expense is less that the date of amount
    # We can only spend on or after the amount date
    if amountIDCheck[1] > convertDateToEpoch(addAnExpenseBody.date):
        response.status_code = status.HTTP_403_FORBIDDEN
        return {"status": "Expense date of " + addAnExpenseBody.date + " cannot be earlier than amount date of " + convertEpochToDate(amountIDCheck[1])}

    # Checks the current amount usage
    # We get all the values by the amount ID and add it into summedUpAmount
    # If the supplied expense + summedUpAmount is greater than the amount value, reject with 403
    # As we cannot spend more than the amount value
    queryToCheckAmountUsage = "SELECT VALUE FROM AMOUNTTRACKER WHERE AMT_ID = ?"
    valuesToCheckAmountUsage = [addAnExpenseBody.amountID]
    currentAmountCheck = cur.execute(
        queryToCheckAmountUsage, valuesToCheckAmountUsage).fetchall()
    extractedNumbers = [number[0] for number in currentAmountCheck]
    summedUpAmount = sum(extractedNumbers)
    if summedUpAmount + addAnExpenseBody.expense > amountIDCheck[2]:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {"status": "Can only add expense of " + str(amountIDCheck[2] - summedUpAmount)}

    # Adds the Expense to the Amount
    queryToAddAnExpense = "INSERT INTO AMOUNTTRACKER (ID, AMT_EXP_DESC, VALUE, TYPE, DATE, AMT_ID) Values (?, ?, ?, ?, ?, ?)"
    generatedIDForExpense = generateID()
    valuesToAddAnExpense = (generatedIDForExpense, sanitizedDescription, addAnExpenseBody.expense,
                            'EXP', convertDateToEpoch(addAnExpenseBody.date), addAnExpenseBody.amountID)
    cur.execute(queryToAddAnExpense, valuesToAddAnExpense)
    connection.commit()
    return {"expenseID": generatedIDForExpense, "status": "Expense of " + str(addAnExpenseBody.expense) + " added.", "amountID": addAnExpenseBody.amountID}


# PUT Body to update an amount
# The amount is validated to be greater than 0


class updateAnAmount(BaseModel):
    amountID: str
    amountDescription: str
    amount: float = Field(gt=0, description="Amount must be greater than 0")
    date: str

# Update an amount endpoint


@app.put("/updateAnAmount")
def updateAnAmount(updateAnAmountBody: updateAnAmount, response: Response):

    # Sanitzes the description
    sanitizedDescription = sanitizeString(
        updateAnAmountBody.amountDescription).strip()

    # Checks the amount description, if its empty returns a 400
    if len(sanitizedDescription) == 0:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"status": "Amount description cannot be empty."}

    # Checks the date format, if its incorrect returns a 400
    if checkDateFormat(updateAnAmountBody.date) == False:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"status": updateAnAmountBody.date + " is not a valid date or is not in DD-MMM-YYYY format, e.g., 05-Aug-2024. Please correct the date."}

    # Connects to the DB
    connection = sqlite3.connect("AMOUNTTRACKER.db")
    cur = connection.cursor()

    # Checks if the supplied amount ID exists in the DB.
    # If there is no amount ID by that ID, it will return NONE, we return with 404
    queryToCheckAmountID = "SELECT ID FROM AMOUNTTRACKER WHERE ID = ? AND TYPE = 'AMT'"
    valuesToCheckAmountID = [updateAnAmountBody.amountID]
    amountIDCheck = cur.execute(
        queryToCheckAmountID, valuesToCheckAmountID).fetchone()
    if amountIDCheck is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"status": "No Amount with the ID " + updateAnAmountBody.amountID + " exists. Please recheck"}

    # Checks the current amount usage and if its less than the value to be updated
    # We get all the values by the amount ID and add it into summedUpAmount
    # If the summedUpAmount is greater than the updated amount value, reject with 403
    # As we cannot update the amount to less that what is already spent
    queryToCheckAmountUsage = "SELECT VALUE FROM AMOUNTTRACKER WHERE AMT_ID = ?"
    valuesToCheckAmountUsage = [updateAnAmountBody.amountID]
    currentAmountCheck = cur.execute(
        queryToCheckAmountUsage, valuesToCheckAmountUsage).fetchall()
    extractedNumbers = [number[0] for number in currentAmountCheck]
    summedUpAmount = sum(extractedNumbers)
    if summedUpAmount > updateAnAmountBody.amount:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {"status": "Total expense for this amount is " + str(summedUpAmount) + ". Cannot update the amount to anything below."}

    # Check expenses date
    queryToCheckExpensesDate = "SELECT DATE FROM AMOUNTTRACKER WHERE AMT_ID = ?"
    checkExpenseDate = cur.execute(
        queryToCheckExpensesDate, valuesToCheckAmountUsage).fetchall()

    # Check if the supplied date, in Epoch, is less than all the expense dates
    # As, the amount date must be less than or equal to the expense dates
    # If the supplied date is less than or equal to all expense dates, return True, else False
    newDateChecker = all(convertDateToEpoch(
        updateAnAmountBody.date) <= item[0] for item in checkExpenseDate)

    # If its False it means that there is one expense date that is less than the supplied amount date, reject with 403
    if newDateChecker is False:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {"status": "Date cannot be updated as there is an expense which is older than the provided date."}

    # Updates the amount description value, date into the DB for the supplied amount ID
    queryToUpdateAnAmount = "UPDATE AMOUNTTRACKER SET AMT_EXP_DESC = ?, VALUE = ?, DATE = ? WHERE ID = ?"
    valuesToUpdateAnAmount = (sanitizedDescription, updateAnAmountBody.amount, convertDateToEpoch(
        updateAnAmountBody.date), updateAnAmountBody.amountID)
    cur.execute(queryToUpdateAnAmount, valuesToUpdateAnAmount)
    connection.commit()
    return {"amountID": updateAnAmountBody.amountID, "status": "Amount updated."}


# PUT Body to update an expense
# The expense is validated to be greater than 0
class updateAnExpense(BaseModel):
    expenseID: str
    expenseDescription: str
    expense: float = Field(gt=0, description="Expense must be greater than 0")
    date: str

# Update an expense endpoint


@app.put("/updateAnExpense")
def updateAnExpense(updateAnExpenseBody: updateAnExpense, response: Response):

    # Sanitzes the description
    sanitizedDescription = sanitizeString(
        updateAnExpenseBody.expenseDescription).strip()

    # Checks the expense description, if its empty returns a 400
    if len(sanitizedDescription) == 0:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"status": "Expense description cannot be empty."}

    # Checks the date format, if its incorrect returns a 400
    if checkDateFormat(updateAnExpenseBody.date) == False:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"status": updateAnExpenseBody.date + " is not a valid date or is not in DD-MMM-YYYY format, e.g., 05-Aug-2024. Please correct the date."}

    # Connects to the DB
    connection = sqlite3.connect("AMOUNTTRACKER.db")
    cur = connection.cursor()

    # Checks if the supplied expense ID exists in the DB.
    # If there is no expense ID by that ID, it will return NONE, we return with 404
    queryToCheckExpenseID = "SELECT ID, AMT_ID FROM AMOUNTTRACKER WHERE ID = ? AND TYPE = 'EXP'"
    valuesToCheckExpenseID = [updateAnExpenseBody.expenseID]
    amountIDCheck = cur.execute(
        queryToCheckExpenseID, valuesToCheckExpenseID).fetchone()
    if amountIDCheck is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"status": "No Expense with the ID " + updateAnExpenseBody.expenseID + " exists. Please recheck"}

    # Checks the current amount usage and if its less than the value to be updated
    # We get all the values by the amount ID excluding the value of the expense to be updated and add it into summedUpAmount
    # Then we get the amount and put it into currentAmountCheck
    # If the summedUpAmount + supplied expense is greater than the amount value, reject with 403
    # As we cannot update the expense to more than the expense
    queryToCheckAmountUsage = "SELECT VALUE FROM AMOUNTTRACKER WHERE AMT_ID = ? AND ID IS NOT ?"
    valuesToCheckAmountUsage = [
        amountIDCheck[1], updateAnExpenseBody.expenseID]
    currentAmountUsageCheck = cur.execute(
        queryToCheckAmountUsage, valuesToCheckAmountUsage).fetchall()
    extractedNumbers = [number[0] for number in currentAmountUsageCheck]
    summedUpAmount = sum(extractedNumbers)

    queryToCheckCurrentAmount = "SELECT VALUE FROM AMOUNTTRACKER WHERE ID = ?"
    valuesToCheckCurrentAmount = [amountIDCheck[1]]
    currentAmountCheck = cur.execute(
        queryToCheckCurrentAmount, valuesToCheckCurrentAmount).fetchone()

    if summedUpAmount + updateAnExpenseBody.expense > currentAmountCheck[0]:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {"status": "Can only update expense to " + str(currentAmountCheck[0] - summedUpAmount)}

    # Get the Amount date of that expense
    queryToGetAmountDate = "SELECT DATE FROM AMOUNTTRACKER WHERE ID = ?"
    checkExpenseDate = cur.execute(
        queryToGetAmountDate, [amountIDCheck[1]]).fetchone()

    # If the provided date is less than the amount's expense date, we reject it
    # Because, the expense date cannot be older than the amount date
    if convertDateToEpoch(updateAnExpenseBody.date) < checkExpenseDate[0]:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {"status": "Date cannot be updated as provided date is older than amount date."}

    # Updates the expense description, value, date into the DB for the supplied expense ID
    queryToUpdateAnExpense = "UPDATE AMOUNTTRACKER SET AMT_EXP_DESC = ?, VALUE = ?, DATE =? WHERE ID = ?"
    valuesToUpdateAnExpense = (sanitizedDescription, updateAnExpenseBody.expense, convertDateToEpoch(
        updateAnExpenseBody.date), updateAnExpenseBody.expenseID)
    cur.execute(queryToUpdateAnExpense, valuesToUpdateAnExpense)
    connection.commit()
    return {"amountID": updateAnExpenseBody.expenseID, "status": "Expense updated."}


# Gets all the available Amount details
# Requires amountID to be sent as a Query param
@app.get("/getAllAmounts")
def getAllAmountDetails(response: Response):

    # Connects to the DB
    connection = sqlite3.connect("AMOUNTTRACKER.db")
    cur = connection.cursor()

    # Query to get the ID, Description, Value of all the Amounts
    queryToGetAmtDetails = "SELECT ID, AMT_EXP_DESC, VALUE, DATE FROM AMOUNTTRACKER WHERE TYPE = 'AMT'"
    amtCheck = cur.execute(queryToGetAmtDetails).fetchall()

    # Check if the amount is present in the DB
    if amtCheck is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"status": "No Amount exists, please create one to get started."}

    # Loop through the amounts
    # We query again to get the no of expenses for each amount
    # Finally everything is appended to a list
    formattedAmount = []
    for ID, AMT_EXP_DESC, VALUE, DATE in amtCheck:
        queryToGetCountOfExpenses = "SELECT COUNT(*) FROM AMOUNTTRACKER WHERE AMT_ID = ?"
        valuesToGetCountOfExpenses = [ID]
        countOfExpensesCheck = cur.execute(
            queryToGetCountOfExpenses, valuesToGetCountOfExpenses).fetchone()
        formattedAmount.append({"amountID": ID, "amountDescription": AMT_EXP_DESC, "amountValue": VALUE,
                               "amountDate": convertEpochToDate(DATE), "noOfExpenses": countOfExpensesCheck[0]})

    # Return the ID, Description, Value and the number of expenses
    return {"amountDetails": formattedAmount}


# Gets all the expense details of an Amount
# Requires amountID to be sent as a Query param
@app.get("/getAmountExpenses")
def getAmountExpenses(response: Response, amountID: str):

    # Connects to the DB
    connection = sqlite3.connect("AMOUNTTRACKER.db")
    cur = connection.cursor()

    # We query 2 times using the supplied amountID
    # queryToGetTotalDetails queries the Value of the Amount
    # queryToGetAmtDetails queries the ID, Description, value of the expenses
    queryToGetTotalDetails = "SELECT VALUE FROM AMOUNTTRACKER WHERE ID = ?"
    valuesToGetAmtDetails = [amountID]
    totalValueCheck = cur.execute(
        queryToGetTotalDetails, valuesToGetAmtDetails).fetchone()
    queryToGetAmtDetails = "SELECT ID, AMT_EXP_DESC, VALUE, DATE FROM AMOUNTTRACKER WHERE AMT_ID = ? "
    noOfExpensesCheck = cur.execute(
        queryToGetAmtDetails, valuesToGetAmtDetails).fetchall()

    # Check if the amount is present in the DB
    if len(totalValueCheck) == 0:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"status": "No Amount with the ID " + amountID + " exists. Please recheck"}

    # Add the values of the expenses
    extractedNumbers = [number[2] for number in noOfExpensesCheck]
    summedUpAmount = sum(extractedNumbers)

    # Subract from the total amount to get the remaining amount
    remainingAmount = totalValueCheck[0] - summedUpAmount

    # Loop through the expenses and append to a list
    formattedExpenses = []
    for ID, AMT_EXP_DESC, VALUE, DATE in noOfExpensesCheck:
        formattedExpenses.append({"expenseID": ID, "expenseDescription": AMT_EXP_DESC,
                                 "expenseValue": VALUE, "expenseDate": convertEpochToDate(DATE)})

    # Return JSON response
    return {"amountID": amountID, "totalAmount": totalValueCheck[0], "totalExpenses": summedUpAmount, "remainingAmount": remainingAmount, "expenseDetails": formattedExpenses}


# Gets all the expense details of an Amount as a chart
# Requires amountID and chartType to be sent as a Query param
@app.get("/getAmountExpensesChart")
def getAmountExpensesChart(amountID: str, chartType: str, request: Request, response: Response):

    if chartType != "pie" and chartType != "bar" and chartType != "doughnut" and chartType != "line" and chartType != "polarArea" and chartType != "radar":
        response.status_code = status.HTTP_403_FORBIDDEN
        return {"status": "Supported chart types are pie, bar, doughnut, line, polarArea and radar"}

    # Connects to the DB
    connection = sqlite3.connect("AMOUNTTRACKER.db")
    cur = connection.cursor()

    # Check if the amount is present in the DB
    queryToGetAmtDetails = "SELECT ID, AMT_EXP_DESC FROM AMOUNTTRACKER WHERE ID = ? AND TYPE = 'AMT'"
    valuesToGetAmtDetails = [amountID]
    amtCheck = cur.execute(queryToGetAmtDetails,
                           valuesToGetAmtDetails).fetchone()

    if amtCheck is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"status": "No Amount with the ID " + amountID + " exists. Please recheck"}

    # Returns a HTML chart
    return templates.TemplateResponse(request=request, name="amountExpenses.html", context={"amountID": amtCheck[0], "amtDesc": amtCheck[1], "chartType": chartType})



# Gets all the amounts with their status, finished or remaining
@app.get("/getAmountStatus")
def getAmountByStatus(response: Response):

    # Connects to the DB
    connection = sqlite3.connect("AMOUNTTRACKER.db")
    cur = connection.cursor()

    # Query to get the ID all the Amounts
    queryToGetAmtDetails = "SELECT ID FROM AMOUNTTRACKER WHERE TYPE = 'AMT'"
    amtCheck = cur.execute(queryToGetAmtDetails).fetchall()

    # Check if the amount is present in the DB
    if amtCheck is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"status": "No Amount exists, please create one to get started."}
    

    # Create an empty list, formattedAmount, to hold the final data
    formattedAmount = []

    # For each Amount ID, get the Value (1st query) and get the expense values (2nd query)
    # Add all the expense values in summedUpExpenses
    # If Value and summedUpExpenses are the same, means the amount is completed, get the ID, Description and Value for that ID and append to the list
    # If Value and summedUpExpenses are not same, means the amount is not finished, get the ID, Description, Value, remaining amount for that ID and append to the list
    index = 0
    while index < len(amtCheck):
        queryToGetValueOfAmount = "SELECT VALUE FROM AMOUNTTRACKER WHERE ID = ?"
        valuesToGetValueOfAmount = amtCheck[index]
        amountValue = cur.execute(queryToGetValueOfAmount, valuesToGetValueOfAmount).fetchone()

        queryToGetExpenseDetails = "SELECT VALUE FROM AMOUNTTRACKER WHERE AMT_ID = ?"
        expenseValue = cur.execute(queryToGetExpenseDetails, valuesToGetValueOfAmount).fetchall()
    
        summedUpExpenses =  sum(item[0] for item in expenseValue)

        queryToDisplayData = "SELECT ID, AMT_EXP_DESC, VALUE FROM AMOUNTTRACKER WHERE ID = ?"
        returnData = cur.execute(queryToDisplayData, valuesToGetValueOfAmount).fetchone()

        if amountValue[0] == summedUpExpenses:
            formattedAmount.append({"amountID": returnData[0], "amountDescription": returnData[1], "amountValue": returnData[2], "amountStatus" : "finished"})

        if amountValue[0] != summedUpExpenses:
            formattedAmount.append({"amountID": returnData[0], "amountDescription": returnData[1], "amountValue": returnData[2], "amountStatus" : "remaining", "remainingAmount" : amountValue[0] - summedUpExpenses})

        index += 1

    # Return the list
    return {"amountDetails": formattedAmount}



# Deletes an amount from the DB, when an amount is deleted all its expenses are also deleted
# Requires amountID to be sent as a Query param
@app.delete("/deleteAmount")
def deleteAmount(amountID: str, response: Response):

    # Connects to the DB
    connection = sqlite3.connect("AMOUNTTRACKER.db")
    cur = connection.cursor()

    # Check if the amount is present in the DB
    queryToCheckAmount = "SELECT * FROM AMOUNTTRACKER WHERE ID = ? AND TYPE = 'AMT'"
    valuesToCheckAmount = [amountID]
    amtCheck = cur.execute(queryToCheckAmount, valuesToCheckAmount).fetchone()

    if amtCheck is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"status": "No Amount with the ID " + amountID + " exists. Please recheck"}

    queryToDeleteAmount = 'DELETE FROM AMOUNTTRACKER WHERE ID = ? OR AMT_ID = ?'
    cur.execute(queryToDeleteAmount, [amountID, amountID])
    connection.commit()
    return {"status": "Amount with the ID, " + amountID + " and all its expenses are deleted."}


# Deletes an expense from the DB
# Requires expenseID to be sent as a Query param
@app.delete("/deleteExpense")
def deleteExpense(expenseID: str, response: Response):

    # Connects to the DB
    connection = sqlite3.connect("AMOUNTTRACKER.db")
    cur = connection.cursor()

    # Check if the expense is present in the DB
    queryToCheckExpense = "SELECT * FROM AMOUNTTRACKER WHERE ID = ? AND TYPE = 'EXP'"
    valuesToCheckExpense = [expenseID]
    expCheck = cur.execute(queryToCheckExpense,
                           valuesToCheckExpense).fetchone()

    if expCheck is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"status": "No Expense with the ID " + expenseID + " exists. Please recheck"}

    queryToDeleteExpense = 'DELETE FROM AMOUNTTRACKER WHERE ID = ? OR AMT_ID = ?'
    cur.execute(queryToDeleteExpense, [expenseID, expenseID])
    connection.commit()
    return {"status": "Expense with the ID, " + expenseID + " is deleted."}


# Deletes all the expenses of an amount
# Requires amountID to be sent as a Query param
@app.delete("/deleteAmountExpenses")
def deleteAmountExpenses(amountID: str, response: Response):

    # Connects to the DB
    connection = sqlite3.connect("AMOUNTTRACKER.db")
    cur = connection.cursor()

    # Check if the amount is present in the DB
    queryToCheckAmount = "SELECT * FROM AMOUNTTRACKER WHERE ID = ? AND TYPE = 'AMT'"
    valuesToCheckAmount = [amountID]
    amtCheck = cur.execute(queryToCheckAmount, valuesToCheckAmount).fetchone()

    if amtCheck is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"status": "No Amount with the ID " + amountID + " exists. Please recheck"}

    queryToDeleteAmountExpenses = 'DELETE FROM AMOUNTTRACKER WHERE AMT_ID = ?'
    cur.execute(queryToDeleteAmountExpenses, [amountID])
    connection.commit()
    return {"status": "All expenses for the Amount with the ID, " + amountID + " are deleted."}