import sqlite3
from fastapi import FastAPI, Response, status
from pydantic import BaseModel, Field
from helpers import *

app = FastAPI()

@app.get("/")
def landingPage():
    return {"message": "Welcome to the Amount Tracker API, being built ..."}


# POST Body to add an amount
# The amount is validated to be greater than 0
class addAnAmount(BaseModel):
    amountDescription : str
    amount : float = Field(gt=0, description = "Amount must be greater than 0")
    date : str

# Add an amount endpoint
@app.post("/addAnAmount")
def addAnAmount(addAnAmountBody: addAnAmount, response: Response):

    # Sanitzes the description 
    # Checks if the date format is correct
    sanitizedDescription = sanitizeString(addAnAmountBody.amountDescription).strip()
    sanitizedDate = checkDateFormat(addAnAmountBody.date)


    # Checks the amount description, if its empty returns a 400
    if len(sanitizedDescription) == 0:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"status" : "Amount description cannot be empty."}


    # Checks the date format, if its incorrect returns a 400
    if sanitizedDate == False:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"status" : addAnAmountBody.date + " is not a valid date or is not in DD-MMM-YYYY format, e.g., 05-Aug-2024. Please correct the date."}
    
    # Connects to the DB
    connection = sqlite3.connect("AMOUNTTRACKER.db")
    cur = connection.cursor()

    # Inserts the amount into the DB and returns the generated ID in the response
    queryToAddAnAmount = "INSERT INTO AMOUNTTRACKER (ID, AMT_EXP_DESC, VALUE, TYPE, DATE) Values (?, ?, ?, ?, ?)"
    generatedIDForAmount = generateID() 
    valuesToAddAnAmount = (generatedIDForAmount, sanitizedDescription, addAnAmountBody.amount,'AMT', convertDateToEpoch(addAnAmountBody.date))
    cur.execute(queryToAddAnAmount, valuesToAddAnAmount)
    connection.commit()
    return {"amountID" : generatedIDForAmount, "status" : "Amount of " + str(addAnAmountBody.amount) + " added."}



# POST Body to add an expense
# The expense is validated to be greater than 0
class addAnExpense(BaseModel):
    amountID : str
    expenseDescription : str
    expense : float = Field(gt=0, description="Expense must be greater than 0")
    date : str


# Add an expense endpoint
@app.post("/addAnExpense")
def addAnExpense(addAnExpenseBody: addAnExpense, response: Response):

    # Sanitzes the description 
    # Checks if the date format is correct
    sanitizedDescription = sanitizeString(addAnExpenseBody.expenseDescription).strip()
    sanitizedDate = checkDateFormat(addAnExpenseBody.date)


    # Checks the expense description, if its empty returns a 400
    if len(sanitizedDescription) == 0:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"status" : "Expense description cannot be empty."}
    

    # Checks the date format, if its incorrect returns a 400
    if sanitizedDate == False:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"status" : addAnExpenseBody.date + " is not a valid date or is not in DD-MMM-YYYY format, e.g., 05-Aug-2024. Please correct the date."}
    

    # Connects to the DB
    connection = sqlite3.connect("AMOUNTTRACKER.db")
    cur = connection.cursor()

    # Checks if the supplied amount ID exists in the DB.
    # We try to fetch the ID, DATE and VALUE from the DB for that ID
    # If there is no amount ID by that ID, it will return NONE, we return with 404
    queryToCheckAmountID = "SELECT ID, DATE, VALUE FROM AMOUNTTRACKER WHERE ID = ? AND TYPE = 'AMT'"
    valuesToCheckAmountID = [addAnExpenseBody.amountID]
    amountIDCheck = cur.execute(queryToCheckAmountID, valuesToCheckAmountID).fetchone()
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
    currentAmountCheck = cur.execute(queryToCheckAmountUsage, valuesToCheckAmountUsage).fetchall()
    extractedNumbers = [number[0] for number in currentAmountCheck]
    summedUpAmount = sum(extractedNumbers)
    if summedUpAmount + addAnExpenseBody.expense > amountIDCheck[2]:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {"status": "Can only add expense of " + str(amountIDCheck[2] - summedUpAmount)}


    # Adds the Expense to the Amount
    queryToAddAnExpense = "INSERT INTO AMOUNTTRACKER (ID, AMT_EXP_DESC, VALUE, TYPE, DATE, AMT_ID) Values (?, ?, ?, ?, ?, ?)"
    generatedIDForExpense = generateID() 
    valuesToAddAnExpense = (generatedIDForExpense, sanitizedDescription, addAnExpenseBody.expense,'EXP', convertDateToEpoch(addAnExpenseBody.date), addAnExpenseBody.amountID)
    cur.execute(queryToAddAnExpense, valuesToAddAnExpense)
    connection.commit()
    return {"expenseID" : generatedIDForExpense, "status" : "Expense of " + str(addAnExpenseBody.expense) + " added.", "amountID" : addAnExpenseBody.amountID}



# PUT Body to update an amount
# The amount is validated to be greater than 0
class updateAnAmount(BaseModel):
    amountID : str
    amountDescription : str
    amount : float = Field(gt=0, description = "Amount must be greater than 0")

# Update an amount endpoint
@app.put("/updateAnAmount")
def updateAnAmount(updateAnAmountBody: updateAnAmount, response: Response):

    # Sanitzes the description 
    sanitizedDescription = sanitizeString(updateAnAmountBody.amountDescription).strip()


    # Checks the amount description, if its empty returns a 400
    if len(sanitizedDescription) == 0:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"status" : "Amount description cannot be empty."}

    
    # Connects to the DB
    connection = sqlite3.connect("AMOUNTTRACKER.db")
    cur = connection.cursor()

    # Checks if the supplied amount ID exists in the DB.
    # If there is no amount ID by that ID, it will return NONE, we return with 404
    queryToCheckAmountID = "SELECT ID FROM AMOUNTTRACKER WHERE ID = ? AND TYPE = 'AMT'"
    valuesToCheckAmountID = [updateAnAmountBody.amountID]
    amountIDCheck = cur.execute(queryToCheckAmountID, valuesToCheckAmountID).fetchone()
    if amountIDCheck is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"status": "No Amount with the ID " + updateAnAmountBody.amountID + " exists. Please recheck"}


    # Checks the current amount usage and if its less than the value to be updated
    # We get all the values by the amount ID and add it into summedUpAmount
    # If the summedUpAmount is greater than the updated amount value, reject with 403
    # As we cannot update the amount to less that what is already spent
    queryToCheckAmountUsage = "SELECT VALUE FROM AMOUNTTRACKER WHERE AMT_ID = ?"
    valuesToCheckAmountUsage = [updateAnAmountBody.amountID]
    currentAmountCheck = cur.execute(queryToCheckAmountUsage, valuesToCheckAmountUsage).fetchall()
    extractedNumbers = [number[0] for number in currentAmountCheck]
    summedUpAmount = sum(extractedNumbers)
    if summedUpAmount > updateAnAmountBody.amount:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {"status": "Total expense for this amount is " + str(summedUpAmount) + ". Cannot update the amount to anything below."}


    # Updates the amount description and value into the DB for the supplied amount ID
    queryToUpdateAnAmount = "UPDATE AMOUNTTRACKER SET AMT_EXP_DESC = ?, VALUE = ? WHERE ID = ?"
    valuesToUpdateAnAmount = (sanitizedDescription, updateAnAmountBody.amount, updateAnAmountBody.amountID)
    cur.execute(queryToUpdateAnAmount, valuesToUpdateAnAmount)
    connection.commit()
    return {"amountID" : updateAnAmountBody.amountID, "status" : "Amount updated."}


# PUT Body to update an expense
# The expense is validated to be greater than 0
class updateAnExpense(BaseModel):
    expenseID : str
    expenseDescription : str
    expense : float = Field(gt=0, description = "Expense must be greater than 0")

# Update an expense endpoint
@app.put("/updateAnExpense")
def updateAnExpense(updateAnExpenseBody: updateAnExpense, response: Response):

    # Sanitzes the description 
    sanitizedDescription = sanitizeString(updateAnExpenseBody.expenseDescription).strip()


    # Checks the expense description, if its empty returns a 400
    if len(sanitizedDescription) == 0:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"status" : "Expense description cannot be empty."}

    
    # Connects to the DB
    connection = sqlite3.connect("AMOUNTTRACKER.db")
    cur = connection.cursor()

    # Checks if the supplied expense ID exists in the DB.
    # If there is no expense ID by that ID, it will return NONE, we return with 404
    queryToCheckExpenseID = "SELECT ID, AMT_ID FROM AMOUNTTRACKER WHERE ID = ? AND TYPE = 'EXP'"
    valuesToCheckExpenseID = [updateAnExpenseBody.expenseID]
    amountIDCheck = cur.execute(queryToCheckExpenseID, valuesToCheckExpenseID).fetchone()
    if amountIDCheck is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"status": "No Expense with the ID " + updateAnExpenseBody.expenseID + " exists. Please recheck"}
    

    # Checks the current amount usage and if its less than the value to be updated
    # We get all the values by the amount ID excluding the value of the expense to be updated and add it into summedUpAmount
    # Then we get the amount and put it into currentAmountCheck

    # If the summedUpAmount + supplied expense is greater than the amount value, reject with 403
    # As we cannot update the expense to more than the expense
    queryToCheckAmountUsage = "SELECT VALUE FROM AMOUNTTRACKER WHERE AMT_ID = ? AND ID IS NOT ?"
    valuesToCheckAmountUsage = [amountIDCheck[1], updateAnExpenseBody.expenseID]
    currentAmountUsageCheck = cur.execute(queryToCheckAmountUsage, valuesToCheckAmountUsage).fetchall()
    extractedNumbers = [number[0] for number in currentAmountUsageCheck]
    summedUpAmount = sum(extractedNumbers)

    queryToCheckCurrentAmount = "SELECT VALUE FROM AMOUNTTRACKER WHERE ID = ?"
    valuesToCheckCurrentAmount = [amountIDCheck[1]]
    currentAmountCheck = cur.execute(queryToCheckCurrentAmount, valuesToCheckCurrentAmount).fetchone()

    if summedUpAmount + updateAnExpenseBody.expense > currentAmountCheck[0]:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {"status": "Can only update expense to " + str(currentAmountCheck[0] - summedUpAmount)}


    # Updates the expense description and value into the DB for the supplied expense ID
    queryToUpdateAnExpense = "UPDATE AMOUNTTRACKER SET AMT_EXP_DESC = ?, VALUE = ? WHERE ID = ?"
    valuesToUpdateAnExpense = (sanitizedDescription, updateAnExpenseBody.expense, updateAnExpenseBody.expenseID)
    cur.execute(queryToUpdateAnExpense, valuesToUpdateAnExpense)
    connection.commit()
    return {"amountID" : updateAnExpenseBody.expenseID, "status" : "Expense updated."}