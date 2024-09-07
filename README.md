# Backend for an Amount Tracking App using FastAPI, SQLite and Python

This repo has the code for an Amount Tracking App Backend. The basic functionality/flow of the app

* You create an amount
* You add expenses to the amount
* You can add expenses until the amount is reached <br><br>

The below REST API endpoints are exposed

* GET /getAllAmounts -- Returns all the available amounts
  
* GET /getAmountExpenses -- Returns all the expense details of an amount
  
* GET /getAmountExpensesChart -- Returns all the expense details of an amount as a Chart

* GET /getAmountStatus -- Returns all the available amounts by their status, i.e. finished or remaining
  
* POST /addAnAmount -- Adds an Amount
  
* POST /addAnExpense -- Adds an expense to an amount
  
* PUT /updateAnAmount -- Updates an amount
  
* PUT //updateAnExpense -- Updates an expense 
  
* DELETE /deleteAmount -- Deletes an amount
  
* DELETE /deleteExpense -- Deletes an expense
  
* DELETE /deleteAmountExpenses -- Deletes all the expenses of an amount <br><br>

The entire suite of endpoints with payloads are available in this HAR, [PythonAmountTracker.har](PythonAmountTracker.har) <br><br>

To run it in Dev mode, use the FastAPI run command

```console
fastapi dev .\index.py
```

Once the app is started locally, the below URL's will be available 

```
API Endpoint URL : http://127.0.0.1:8000 
Generated API Docs URL : http://127.0.0.1:8000/docs
```
