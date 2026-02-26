IQVIA – National Prescription Opioid Data
Overview
This project’s data is stored in a PostgreSQL server and consists of 4 primary tables designed to track prescriptions filled in pharmacies, how payment was made, and the prescribing physician from 1997 to 2018. 

Schema
Table Definitions
drug: Data on every prescription written. Contains 4,067 rows and 8 columns.
Column Name
Description
Type
pg
Unique ID
Numeric
description
Drug description
Text
active_ingredient
Active ingredient
Text
milligrams_per_unit
Dosage in mg
Numeric
mme_per_unit
Equivalent dosage amount as morphine
Numeric
dosage_strength
Prescribed amount
Text
dosage_type
Type prescription
Text
usc
Drug class
*All opioids start with 022
Text


main: Main data table. Every row reflects an individual prescription. DO NOT TRY TO DOWNLOAD THIS ENTIRE TABLE. There are 2,125,722,049 total rows and 10 columns.
Column Name
Description
Type
prescriber_key
Unique prescriber ID
Numeric
payor_plan_id
Payment ID
Numeric
sales_category
Sales type
1 = Retail
2 = Mail Order
Numeric
pg
Unique ID
Numeric
year
Year
Numeric
month
Month
Numeric
new_rx
Number new prescriptions 
*Must divide by 1000
Numeric
total_rx
Number total prescriptions 
*Must divide by 1000
Numeric
new_qty
Number new amount 
*Must divide by 1000
Numeric
total_qty
Number total amount 
*Must divide by 1000
Numeric


payor_plan: Details on payment type. Consists of 15,088 rows and 3 columns.
Column Name
Description
Type
payor_plan_id
Payment ID
Numeric
payor_plan
Payment type
Text
payor_plan_var
Payment type variant
Text


prescriber_limited: Prescriber details. There are 1,958,685 rows and 5 columns.
Column Name
Description
Type
prescriber_key
Unique prescriber ID
*unique to prescriber and their location
Numeric
imsid
Prescriber ID
*same for prescriber regardless of location
Numeric
specialty
Prescriber specialty
Text
state
State abbreviation
Text
zip_code
Zip code
Text



Setup & Access
You need to be on ND’s wifi to access the data server.
Host: lucy-iqvia-db.c61zpvuf4ib1.us-east-1.rds.amazonaws.com
Port: 5432 
Database Name: postgres
User: student_read_only_limited
Password: studentuseriqvialogin
Recommended Tools: R, Python, DBeaver, or psql via terminal.

SQL Intro
Regardless of which Program you use to access the server, you’ll need to know some basic SQL to download the data.
SQL queries are written in three parts:
	SELECT [column names] FROM [data table name] WHERE [conditions to meet]
1. SELECT This is used to select the columns from the data table. You can choose:
Specific Columns: List only the names of columns you want.
All Columns: Use the asterisk (*) to see everything in the table.
2. FROM Select which table to use.
3. The WHERE part is not mandatory, but is used for filtering the data by using logic.
Key filtering operations are:
Standard operators 
Symbol
Means
Example
=
Equals
month = 10
<
Less than
month < 10
>
Greater than
month > 10
<=
Less than or equal to
month <= 10
>=
Greater than or equal to
month >= 10
<>
Not equal to
month <> 10
Other Operators


AND
this AND that
month = 10 AND year = 1997
OR
this OR that
month = 10 OR year = 1998
IN
in a list
month IN (1, 2, 12)
BETWEEN
in a range
month BETWEEN 1 AND 5
IS NULL
is missing
month IS NULL




Potential Starting Research Queries
Prescriber preferences: How are prescribers and the brand or type of drug that is prescribed related?
Drug types over time: What is the relation between time and the type of drug prescribed?
Dosage amounts over time: How does the rate of the dosage of prescriptions change over time?

