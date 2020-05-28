### capNrep Installation Guide

## Steps after you clone our project
1- Install androidViewClient from https://github.com/dtmilano/AndroidViewClient , you can follow installations in here
2- After you download androidViewClient, go to Users/<username>/Library/Python/2.7/bin folder copy this culebra3 file under culebra_files.
3- After that go to /Users/<username>/Library/Python/2.7/lib/python/site-packages/com/dtmilano/android and copy culebron3 file under culebra_files.
4- Then open culebron3 file which is inside of /Users/<username>/Library/Python/2.7/lib/python/site-packages/com/dtmilano/android folder then search for #mali, you should find 2 things inside of it. Then ```file = open("/Users/caner/Desktop/capNrep/currentRecord.txt","w") #mali``` change path for your currentRecord.txt which is inside of project. Also change path for this as well ```with open("/Users/caner/Desktop/capNrep/currentRecord.txt", "a") as fp:``` After that save file and exit. You are done with this file.
5- you should download missing packages for this project. 
6- now you are ready to go. run your project with ```python3 capNrep.py``` on terminal. You should see our UI :) Enjoy
Extra notes:
-> you should run emulator or any other android device before open culebra on our UI.

## Dependencies
1- Download culebra with python version 2.7
2- Run our project with python version 3.7