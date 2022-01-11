The project folder contains these 3 files:

connect.py - This is the python script that check for the ssh connection is open or not, if connection is open check for available space if free space is above 20% send main , else it will send mail to the given mail id, which can be changed in the .env file

requirements.txt - This contains list of modules that is necessary for the python script to work.

.env - This file contains all the details about SSh connection like username, password, host and also email details of sender and recipient. All of which can be edited within this env file.

Finally it can be added to the windows Task Scheduler to run the specific time intervals like every 10 minutes, 15 minutes.. etc

p.s.: Don't forget to "pip install -r requirements.txt" to install the dependency for this code to run.
