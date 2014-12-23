#couldnt get this thing to work
#!/usr/bin/env python
# coding=utf-8
# Mobile Numbering system in India
# http://en.wikipedia.org/wiki/Mobile_telephone_numbering_in_India
#
# STD Codes are sourced from
# STDCodes.csv
#
#################################################################################
import sys
import sqlite3 as lite
import requests
import time
from BeautifulSoup import BeautifulSoup
import dataset
import time
import datetime
import csv
from easygui import *

msg = "Enter Exotel Details"
title = "Enter Exotel Details"
fieldNames = ["Exotel SID","Exotel Token"]
fieldValues = []  # we start with blanks for the values
fieldValues = multenterbox(msg,title, fieldNames)

while 1:
    if fieldValues == None: break
    errmsg = ""
    for i in range(len(fieldNames)):
      if fieldValues[i].strip() == "":
        errmsg = errmsg + ('"%s" is a required field.\n\n' % fieldNames[i])
    if errmsg == "": break # no problems found
    fieldValues = multenterbox(errmsg, title, fieldNames, fieldValues)


exotel_sid = fieldValues[0] 
exotel_token = fieldValues[1] 


print "exotel_sid="+str(exotel_sid)
print "exotel_token="+str(exotel_token)

csv_file_names = fileopenbox("Please select CSV with phone numbers.")

print "File name is"+str(csv_file_names)



if exotel_sid:
    
    basic_url ="https://{exotel_sid}:{exotel_token}@twilix.exotel.in/v1/Accounts/{exotel_sid}/Numbers/{phoneNumber}"
    db = dataset.connect('sqlite:///./database/db.sqlite')
    db.begin()
    phone_metadata = db['phone_metadata']

    msg = "Is this a Re-run or Fresh Run?"
    choices = ["Rerun","Fresh"]
    reply = buttonbox(msg,  choices=choices)
    if reply == "Fresh":
        phone_metadata.delete()
    
    first_line = True
    with open(csv_file_names, 'rb') as csvfile:
       csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
       for row in csvreader:
           if first_line:
               first_line = False
               continue
           name = str(row[0])
           company = str(row[1])        
           number = str(row[2])
           email =str(row[3])
           date_of_addition = str(row[4])
           if phone_metadata.find_one(PhoneNumber=number):
               pass
           else:
               print "inserting"
               phone_metadata.insert(dict(PhoneNumber=number, date_of_addition=date_of_addition, name=name, email=email))
    db.commit()        
    print "Total phone nos inside the database ="+str(len(phone_metadata))

    while 1:
        get_phone = db.query('SELECT * FROM phone_metadata  where scraped=0 LIMIT 1')
        my_list = list(get_phone)    
        if len(my_list) > 0:
            phoneNumber = my_list[0]['PhoneNumber']
            print "processing number"+str(phoneNumber)
            url = basic_url.format(phoneNumber=phoneNumber,exotel_sid=exotel_sid,exotel_token=exotel_token)
            print url
            xml_get_src = requests.get(url)
            #print xml_get_src.content
            soup = BeautifulSoup(xml_get_src.content)
            exceptions = soup.find("restexception")
            if exceptions:
                status = exceptions.find("status")
                scraped = status.string
                print status.string
                print "!!**************** There were exceptions and hence shutting down ****************!!"
                break
            
            #print str(soup)
            numbers = soup.find("numbers")
            print str(numbers)
            if numbers:
                print "getting answers from the system"
                try:
                    print str(numbers.find("circle").contents[0])
                except:
                    print "Error -- Updating status 2"
                    data_update = dict(PhoneNumber=str(phoneNumber),scraped=2)
                    phone_metadata.update(data_update, ['PhoneNumber'])        
                    db.commit()
                    continue
                    
                #Template of the response
                #<Numbers>
                #<PhoneNumber>08686888888 </PhoneNumber>
                #<Circle>AP</Circle>
                Circle = numbers.find("circle").contents[0]
                #<CircleName>Andhra Pradesh Telecom Circle</CircleName>
                CircleName = numbers.find("circlename").contents[0]

                #<Type>Mobile</Type>
                Type = numbers.find("type").contents[0]
                if Type=="Landline":
                    pass
                    
                #<Operator>AC</Operator>
                Operator = ""
                if len(numbers.find("operator").contents) > 0:
                    Operator = numbers.find("operator").contents[0]
                

                #<OperatorName>Aircel</OperatorName>
                OperatorName = numbers.find("operatorname").contents[0]

                #<DND>No</DND>
                DND = numbers.find("dnd").contents[0]
                #</Numbers>
                data_update = dict(PhoneNumber=str(phoneNumber),Circle=Circle,CircleName=CircleName,Type=Type,Operator=Operator,OperatorName=OperatorName,DND=DND,scraped=1)
                print str(data_update)
                phone_metadata.update(data_update, ['PhoneNumber'])        
                db.commit()

        else:
            print "\t --No phones to continue..."
            break

    result_csv_file_names = filesavebox("Please give a name to save the updated csv file.")
    result = phone_metadata.all()
    fh = open(result_csv_file_names, 'wb')
    dataset.freeze(result, format='csv', filename=result_csv_file_names, fileobj=fh)
else:
    print "Exit: Error, config parameters are not set properly"