import json
import os
import queue
import re
import subprocess
import threading
import watchdog
import copy
import threading 
from tkinter import *
from tkinter import ttk

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

isFileInitiated = False

counter = 0


class ThreadedTask(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        self.queue.put("Task finished")


class VerticalScrolledFrame(Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling

    """

    def __init__(self, parent, *args, **kw):
        Frame.__init__(self, parent, *args, **kw)

        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = Scrollbar(self, orient=VERTICAL)
        vscrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)
        canvas = Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=vscrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        vscrollbar.config(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())

        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())

        canvas.bind('<Configure>', _configure_canvas)


class CaptureAndReplay:

    def __init__(self, master=None):

        self.databaseChanged = False  # if a new statement is added it will be true
        self.currentEvents = []  # Current recorded actions in array as this format => {"action":"code"}
        self.autoEntryCount = 50  # GHERKIN AREA
        self.autoEntryList = []  # GHERKIN AREA LIST OF AUTOENTRIES
        self.out_filename = "default"  # DEFAULT NAME OF THE FILE
        self.queue = queue.Queue()
        self.window = master
        self.event_handler = watchdog.events.FileSystemEventHandler()
        self.event_handler.on_modified = self.on_modified
        self.observer = Observer()
        
        self.observer.schedule(self.event_handler, path="/Users/caner/Desktop/capNrep/", recursive=False) # mali
        self.observer.start()
        self.checkPopUpIsOpen = False
        self.actionTypeSet = "Action"

        with open("database.json", "r") as fp:
            self.database = json.load(fp)

        self.createButtons()
        self.nb = ttk.Notebook(self.window)
        self.nb.grid(row=0, column=0, columnspan=35, rowspan=50, sticky='NSEW')

        self.currentRecord = ttk.Frame(self.nb)
        self.nb.add(self.currentRecord, text="CURRENT RECORD")

        self.testArea = ttk.Frame(self.nb)
        self.nb.add(self.testArea, text="TEST AREA")

        self.gherkinTestArea = VerticalScrolledFrame(self.nb)
        self.nb.add(self.gherkinTestArea, text="GHERKIN")

        self.allLibrary = ttk.Frame(self.nb)
        self.nb.add(self.allLibrary, text="FROM LIBRARY")

        rows = 0
        while rows < 50:
            self.testArea.rowconfigure(rows, weight=1)
            self.testArea.columnconfigure(rows, weight=1)
            rows += 1

        self.givenLabel = Label(self.testArea,
                                text="GIVEN:",
                                anchor=W,
                                background="red")
        self.givenLabel.pack(fill=X, side=TOP)

        self.givenList = Listbox(self.testArea, height=9)
        self.givenList.pack(fill=X, side=TOP)

        self.whenLabel = Label(self.testArea,
                               text="WHEN:",
                               anchor=W,
                               background="blue")
        self.whenLabel.pack(fill=X, side=TOP)

        self.whenList = Listbox(self.testArea, height=9)
        self.whenList.pack(fill=X, side=TOP)

        self.thenLabel = Label(self.testArea,
                               text="THEN:",
                               anchor=W,
                               background="yellow")
        self.thenLabel.pack(fill=X, side=TOP)

        self.thenList = Listbox(self.testArea, height=9)
        self.thenList.pack(fill=X, side=TOP)

        self.currentRecordLabel = Label(self.currentRecord,
                                        text="CURRENT RECORD:",
                                        anchor=W,
                                        background="yellow")
        self.currentRecordLabel.pack(fill=X, side=TOP)

        self.currentEventsList = Listbox(self.currentRecord,
                                         height=30,
                                         listvariable=self.currentEvents,
                                         selectmode='multiple')
        self.currentEventsList.pack(fill=X, side=TOP)

        for x in range(self.autoEntryCount):
            autocomp = AutocompleteEntry(self.database, self.gherkinTestArea.interior, listboxLength=10, width=65)
            autocomp.grid(row=x, column=0)
            self.autoEntryList.append(autocomp)

        self.libraryEventLabel = Label(self.allLibrary,
                                       text="LIBRARY:",
                                       anchor=W,
                                       background="red")
        self.libraryEventLabel.pack(fill=X, side=TOP)

        self.databaseEventsList = Listbox(self.allLibrary,
                                          height=30,
                                          selectmode='multiple')
        self.databaseEventsList.pack(fill=X, side=TOP)

        self.updateDatabaseEventsList()

        rows = 0
        while rows < 50:
            self.window.rowconfigure(rows, weight=1)
            self.window.columnconfigure(rows, weight=1)
            rows += 1

    def on_modified(self, event):
        if event.src_path.find("currentRecord.txt") > 0:
            global isFileInitiated
            if isFileInitiated:
                self.callBDDDialog()

            if not isFileInitiated:
                isFileInitiated = True

    def openCulebraGUI(self):
        global isFileInitiated
        isFileInitiated = False
        subprocess.call(["adb", "devices"])
        subprocess.Popen(["culebra3", "--scale=0.4", "-uUG"])

        # WHEN CALL CULEBRA WITH THESE LINES OF CODE.
        # CULEBRA AND OUR UI DOES NOT WORK CONCURRENTLY
        # THEREFORE WE USE subprocess.Popen()

        # subprocess.call(["culebra3", "--scale=0.4","-uUG","-o","temp.py"])
        # os.system("adb devices && culebra3 --scale=0.4 -uUG -o temp.py")

    def moveToGivenArea(self):

        selectedItemsFromCurrentEvents = self.currentEventsList.curselection()
        selectedItemsFromLibrary = self.databaseEventsList.curselection()

        if selectedItemsFromCurrentEvents != ():
            self.showSaveActionDialog(actionType="Given")

        if selectedItemsFromLibrary != ():
            for selectedItem in selectedItemsFromLibrary:
                self.givenList.insert(END, self.database[str(selectedItem)]['action_name'])

    def moveToWhenArea(self):

        selectedItemsFromCurrentEvents = self.currentEventsList.curselection()
        selectedItemsFromLibrary = self.databaseEventsList.curselection()

        if selectedItemsFromCurrentEvents != ():
            self.showSaveActionDialog(actionType="When")

        if selectedItemsFromLibrary != ():
            for selectedItem in selectedItemsFromLibrary:
                self.whenList.insert(END, self.database[str(selectedItem)]['action_name'])

    def moveToThenArea(self):

        selectedItemsFromCurrentEvents = self.currentEventsList.curselection()
        selectedItemsFromLibrary = self.databaseEventsList.curselection()

        if selectedItemsFromCurrentEvents != ():
            self.showSaveActionDialog(actionType="Then")

        if selectedItemsFromLibrary != ():
            for selectedItem in selectedItemsFromLibrary:
                self.thenList.insert(END, self.database[str(selectedItem)]['action_name'])

    def updateCurrentEventsList(self):

        self.currentEventsList.delete(0, END)  # clear listbox
        for event in self.currentEvents:  # populate listbox again #mali DONE
            for key in event.keys():
                self.currentEventsList.insert(END, key)

    def updateDatabaseEventsList(self):
        self.databaseEventsList.delete(0, END)
        for event in self.database.keys():  # populate listbox again
            self.databaseEventsList.insert(END, self.database[event]['action_type'] + " " + self.database[event][
                'action_name'])

    def moveUp(self):

        moveFromGivenList = self.givenList.curselection()
        moveFromWhenList = self.whenList.curselection()
        moveFromThenList = self.thenList.curselection()

        if moveFromGivenList != ():
            for pos in moveFromGivenList:
                if pos == 0:
                    continue
                text = self.givenList.get(pos)
                self.givenList.delete(pos)
                self.givenList.insert(pos - 1, text)
                self.givenList.selection_set(pos - 1)

        if moveFromWhenList != ():
            for pos in moveFromWhenList:
                if pos == 0:
                    continue
                text = self.whenList.get(pos)
                self.whenList.delete(pos)
                self.whenList.insert(pos - 1, text)
                self.whenList.selection_set(pos - 1)

        if moveFromThenList != ():
            for pos in moveFromThenList:
                if pos == 0:
                    continue
                text = self.thenList.get(pos)
                self.thenList.delete(pos)
                self.thenList.insert(pos - 1, text)
                self.thenList.selection_set(pos - 1)

    def moveDown(self):

        moveFromGivenList = self.givenList.curselection()
        moveFromWhenList = self.whenList.curselection()
        moveFromThenList = self.thenList.curselection()

        if moveFromGivenList != ():
            for pos in moveFromGivenList:
                if pos == self.givenList.size() - 1:
                    continue
                text = self.givenList.get(pos)
                self.givenList.delete(pos)
                self.givenList.insert(pos + 1, text)
                self.givenList.selection_set(pos + 1)

        if moveFromWhenList != ():
            for pos in moveFromWhenList:
                if pos == self.whenList.size() - 1:
                    continue
                text = self.whenList.get(pos)
                self.whenList.delete(pos)
                self.whenList.insert(pos + 1, text)
                self.whenList.selection_set(pos + 1)

        if moveFromThenList != ():
            for pos in moveFromThenList:
                if pos == self.thenList.size() - 1:
                    continue
                text = self.thenList.get(pos)
                self.thenList.delete(pos)
                self.thenList.insert(pos + 1, text)
                self.thenList.selection_set(pos + 1)

    def removeElement(self):

        moveFromGivenList = self.givenList.curselection()
        moveFromWhenList = self.whenList.curselection()
        moveFromThenList = self.thenList.curselection()
        moveFromCurrentList = self.currentEventsList.curselection()
        if moveFromGivenList != ():
            for pos in moveFromGivenList:
                self.givenList.delete(pos)

        if moveFromWhenList != ():
            for pos in moveFromWhenList:
                self.whenList.delete(pos)

        if moveFromThenList != ():
            for pos in moveFromThenList:
                self.thenList.delete(pos)

        if moveFromCurrentList != ():
            for pos in moveFromCurrentList:
                self.currentEvents.remove(self.currentEvents[pos])
                self.currentEventsList.delete(pos)
    
    def parametrizeElement(self):
        counter = 0 

        def on_closing():
            self.checkPopUpIsOpen = False
            popup.destroy()

        parametrizeFromGivenList = self.givenList.curselection()
        parametrizeFromWhenList = self.whenList.curselection()
        parametrizeFromThenList = self.thenList.curselection()
        if parametrizeFromGivenList == () and parametrizeFromWhenList == () and parametrizeFromThenList == ():
            return
        if self.checkPopUpIsOpen == True:
            return
        self.checkPopUpIsOpen = True
        # Given
        if parametrizeFromGivenList != ():
            popup = Toplevel()
            popup.geometry("700x300+550+350")
            popup.lift()
            popup.attributes('-topmost', True)
            popup.protocol("WM_DELETE_WINDOW", on_closing)
            actionName = self.givenList.get(parametrizeFromGivenList[0])
            indexOnDb = ""
            for key in self.database.keys():
                if self.database[key]["action_name"] == actionName:
                    indexOnDb = key
            codeDictionary = self.database[indexOnDb]["codes"]
            filenameInputTexts = []

            counter = 0
            for index in codeDictionary:
                label = Label(popup, text=codeDictionary[index], anchor=W)
                label.pack(fill='x')

                filenameInputTexts.append(Entry(popup))
                filenameInputTexts[counter].pack(fill='x')
                counter += 1
            def saveNewParametrizes():
                nonlocal counter
                counter -= 1
                quotesString = "'''"
                quoteString = "'"
                tirnakString ="\""
                counterOfParametrizationIndex = 0
                temp = copy.deepcopy(self.database[indexOnDb])
                lenDbString = str(len(self.database))
                for filenameInputText in filenameInputTexts:
                    text = filenameInputText.get()
                    if text != "":
                        self.database[lenDbString] = self.database[indexOnDb]
                        # for codes 
                        codeDictionary = self.database[lenDbString]["codes"]
                        findFirstIndex = codeDictionary[str(counter)].find(quotesString)
                        findSecondIndex = codeDictionary[str(counter)].find(quotesString,findFirstIndex+len(quotesString))
                        parametrizedWord = codeDictionary[str(counter)][findFirstIndex + len(quotesString):findSecondIndex]
                        codeDictionary[str(counter)] = codeDictionary[str(counter)].replace(parametrizedWord, text)
                        # for action name
                        actionDictionary = self.database[lenDbString]["action_name"]
                        findFirstIndex = actionDictionary.find(tirnakString,counterOfParametrizationIndex)
                        if findFirstIndex != -1:
                            findSecondIndex = actionDictionary.find(tirnakString,findFirstIndex+len(tirnakString))
                            parametrizedWord = actionDictionary[findFirstIndex + len(tirnakString):findSecondIndex]
                            counterOfParametrizationIndex = findSecondIndex + 1 +len(text) - len(parametrizedWord) 
                            self.database[lenDbString]["action_name"] = actionDictionary.replace("\"" + parametrizedWord + "\"", "\"" + text + "\"")
                        else:
                            findFirstIndex = actionDictionary.find(quoteString,counterOfParametrizationIndex)
                            if findFirstIndex != -1:
                                findSecondIndex = actionDictionary.find(quoteString,findFirstIndex+len(quoteString))
                                parametrizedWord = actionDictionary[findFirstIndex + len(quoteString):findSecondIndex]
                                counterOfParametrizationIndex = findSecondIndex + 1 +len(text) - len(parametrizedWord) 
                                self.database[lenDbString]["action_name"] = actionDictionary.replace("'" + parametrizedWord + "'", "'" + text + "'")               
                    counter -= 1
                self.database[lenDbString] = temp    
                tempList = []
                for i in range(self.givenList.size()):
                    tempList.append(self.givenList.get(i))
                self.givenList.delete(0, END)  # clear listbox
                for i in range(len(tempList)):
                    if i == parametrizeFromGivenList[0]:
                        self.givenList.insert(END, self.database[indexOnDb]['action_name'])
                    else:
                        self.givenList.insert(END, tempList[i])
                self.updateDatabaseEventsList()
                self.checkPopUpIsOpen = False
                popup.destroy()
                
                


            
            saveButton = Button(popup, text="Save", command=saveNewParametrizes)
            saveButton.pack(fill='x')
        
        # When
        if parametrizeFromWhenList != ():
            popup = Toplevel()
            popup.geometry("700x300+550+350")
            popup.lift()
            popup.attributes('-topmost', True)
            popup.protocol("WM_DELETE_WINDOW", on_closing)
            actionName = self.whenList.get(parametrizeFromWhenList[0])
            indexOnDb = ""
            for key in self.database.keys():
                if self.database[key]["action_name"] == actionName:
                    indexOnDb = key
            codeDictionary = self.database[indexOnDb]["codes"]
            filenameInputTexts = []

            counter = 0
            for index in codeDictionary:
                label = Label(popup, text=codeDictionary[index], anchor=W)
                label.pack(fill='x')

                filenameInputTexts.append(Entry(popup))
                filenameInputTexts[counter].pack(fill='x')
                counter += 1
            def saveNewParametrizes():
                nonlocal counter
                counter -= 1
                quotesString = "'''"
                quoteString = "'"
                counterOfParametrizationIndex = 0
                temp = copy.deepcopy(self.database[str(parametrizeFromWhenList[0])])
                lenDbString = str(len(self.database))
                for filenameInputText in filenameInputTexts:
                    text = filenameInputText.get()
                    if text != "":
                        self.database[lenDbString] = self.database[str(parametrizeFromWhenList[0])]
                        # for codes 
                        codeDictionary = self.database[lenDbString]["codes"]
                        findFirstIndex = codeDictionary[str(counter)].find(quotesString)
                        findSecondIndex = codeDictionary[str(counter)].find(quotesString,findFirstIndex+len(quotesString))
                        parametrizedWord = codeDictionary[str(counter)][findFirstIndex + len(quotesString):findSecondIndex]
                        codeDictionary[str(counter)] = codeDictionary[str(counter)].replace(parametrizedWord, text)
                        # for action name
                        actionDictionary = self.database[lenDbString]["action_name"]
                        findFirstIndex = actionDictionary.find(quoteString,counterOfParametrizationIndex)
                        if findFirstIndex != -1:
                            findSecondIndex = actionDictionary.find(quoteString,findFirstIndex+len(quoteString))
                            parametrizedWord = actionDictionary[findFirstIndex + len(quoteString):findSecondIndex]
                            counterOfParametrizationIndex = findSecondIndex + 1 +len(text) - len(parametrizedWord) 
                            self.database[lenDbString]["action_name"] = actionDictionary.replace("'" + parametrizedWord + "'", "'" + text + "'")                
                    counter -= 1
                self.database[lenDbString] = temp    
                tempList = []
                for i in range(self.whenList.size()):
                    tempList.append(self.whenList.get(i))
                self.whenList.delete(0, END)  # clear listbox
                for i in range(len(tempList)):
                    if i == parametrizeFromWhenList[0]:
                        self.whenList.insert(END, self.database[str(parametrizeFromWhenList[0])]['action_name'])
                    else:
                        self.whenList.insert(END, tempList[i])
                self.updateDatabaseEventsList()
                self.checkPopUpIsOpen = False
                popup.destroy()
                
                


            
            saveButton = Button(popup, text="Save", command=saveNewParametrizes)
            saveButton.pack(fill='x')
        
        # Then
        if parametrizeFromThenList != ():
            popup = Toplevel()
            popup.geometry("700x300+550+350")
            popup.lift()
            popup.attributes('-topmost', True)
            popup.protocol("WM_DELETE_WINDOW", on_closing)
            actionName = self.thenList.get(parametrizeFromThenList[0])
            indexOnDb = ""
            for key in self.database.keys():
                if self.database[key]["action_name"] == actionName:
                    indexOnDb = key
            codeDictionary = self.database[indexOnDb]["codes"]
            filenameInputTexts = []

            counter = 0
            for index in codeDictionary:
                label = Label(popup, text=codeDictionary[index], anchor=W)
                label.pack(fill='x')

                filenameInputTexts.append(Entry(popup))
                filenameInputTexts[counter].pack(fill='x')
                counter += 1
            def saveNewParametrizes():
                nonlocal counter
                counter -= 1
                quotesString = "'''"
                quoteString = "'"
                counterOfParametrizationIndex = 0
                temp = copy.deepcopy(self.database[str(parametrizeFromThenList[0])])
                lenDbString = str(len(self.database))
                for filenameInputText in filenameInputTexts:
                    text = filenameInputText.get()
                    if text != "":
                        self.database[lenDbString] = self.database[str(parametrizeFromThenList[0])]
                        # for codes 
                        codeDictionary = self.database[lenDbString]["codes"]
                        findFirstIndex = codeDictionary[str(counter)].find(quotesString)
                        findSecondIndex = codeDictionary[str(counter)].find(quotesString,findFirstIndex+len(quotesString))
                        parametrizedWord = codeDictionary[str(counter)][findFirstIndex + len(quotesString):findSecondIndex]
                        codeDictionary[str(counter)] = codeDictionary[str(counter)].replace(parametrizedWord, text)
                        # for action name
                        actionDictionary = self.database[lenDbString]["action_name"]
                        findFirstIndex = actionDictionary.find(quoteString,counterOfParametrizationIndex)
                        if findFirstIndex != -1:
                            findSecondIndex = actionDictionary.find(quoteString,findFirstIndex+len(quoteString))
                            parametrizedWord = actionDictionary[findFirstIndex + len(quoteString):findSecondIndex]
                            counterOfParametrizationIndex = findSecondIndex + 1 +len(text) - len(parametrizedWord) 
                            self.database[lenDbString]["action_name"] = actionDictionary.replace("'" + parametrizedWord + "'", "'" + text + "'")                
                    counter -= 1
                self.database[lenDbString] = temp    
                tempList = []
                for i in range(self.thenList.size()):
                    tempList.append(self.thenList.get(i))
                self.thenList.delete(0, END)  # clear listbox
                for i in range(len(tempList)):
                    if i == parametrizeFromThenList[0]:
                        self.thenList.insert(END, self.database[str(parametrizeFromThenList[0])]['action_name'])
                    else:
                        self.thenList.insert(END, tempList[i])
                self.updateDatabaseEventsList()
                self.checkPopUpIsOpen = False
                popup.destroy()
                
                


            
            saveButton = Button(popup, text="Save", command=saveNewParametrizes)
            saveButton.pack(fill='x')

        self.updateDatabaseEventsList()
        

    def writeHeader(self):

        with open("header.txt") as fp:
            line = fp.readline()
            with open(self.out_filename + ".py", 'w') as out_file:
                while line:
                    out_file.write(line)
                    line = fp.readline()

    def generateTestFromEvents(self):

        isGivenExist = self.givenList.size() > 0
        isWhenExist = self.whenList.size() > 0
        isThenExist = self.thenList.size() > 0

        with open(self.out_filename + ".py", "a") as out_file:
            out_file.write('\n\n')
            if isGivenExist:
                for i in range(self.givenList.size()):
                    for key in self.database:
                        if self.database[key]['action_name'] == self.givenList.get(i) and self.database[key]['action_type'] == 'Given':
                            for codeKey in self.database[key]['codes']:
                                out_file.write("        self.vc.dump(window=-1)\n")
                                out_file.write("        " + self.database[key]['codes'][codeKey].strip() + '\n')
                                out_file.write("        self.vc.sleep(_s)\n")

            if isWhenExist:
                for i in range(self.whenList.size()):
                    for key in self.database:
                        if self.database[key]['action_name'] == self.whenList.get(i) and self.database[key][
                            'action_type'] == 'When':
                            for codeKey in self.database[key]['codes']:
                                out_file.write("        self.vc.dump(window=-1)\n")
                                out_file.write("        " + self.database[key]['codes'][codeKey].strip() + '\n')
                                out_file.write("        self.vc.sleep(_s)\n")

            if isThenExist:
                for i in range(self.thenList.size()):
                    for key in self.database:
                        if self.database[key]['action_name'] == self.thenList.get(i) and self.database[key][
                            'action_type'] == 'Then':
                            for codeKey in self.database[key]['codes']:
                                out_file.write("        self.vc.dump(window=-1)\n")
                                out_file.write("        " + self.database[key]['codes'][codeKey].strip() + '\n')
                                out_file.write("        self.vc.sleep(_s)\n")

    def writeFooter(self):
        with open("footer.txt") as fp:
            line = fp.readline()
            with open(self.out_filename + ".py", 'a') as out_file:
                out_file.write('\n\n')
                while line:
                    out_file.write(line)
                    line = fp.readline()

    def writeGherkinHeader(self):

        with open("gherkinHeader.txt") as fp:
            line = fp.readline()
            with open(self.out_filename + ".feature", "w") as out_file:
                while line:
                    out_file.write(line)
                    line = fp.readline()

    def generateGherkinTestFromEvents(self):

        isGivenExist = self.givenList.size() > 0
        isWhenExist = self.whenList.size() > 0
        isThenExist = self.thenList.size() > 0

        with open(self.out_filename + ".feature", "a") as out_file:
            out_file.write('\n\n')
            if isGivenExist:
                for i in range(self.givenList.size()):
                    event = self.givenList.get(i)
                    if i == 0:
                        out_file.write("\t\tGiven " + event.strip() + '\n')
                    else:
                        out_file.write("\t\tAnd " + event.strip() + '\n')

            if isWhenExist:
                for i in range(self.whenList.size()):
                    event = self.whenList.get(i)
                    if i == 0:
                        out_file.write("\t\tWhen " + event.strip() + '\n')
                    else:
                        out_file.write("\t\tAnd " + event.strip() + '\n')

            if isThenExist:
                for i in range(self.thenList.size()):
                    event = self.thenList.get(i)
                    if i == 0:
                        out_file.write("\t\tThen " + event.strip() + '\n')
                    else:
                        out_file.write("\t\tAnd " + event.strip() + '\n')

    def openSaveTestDialog(self):

        popup = Toplevel()
        popup.geometry("300x100+550+350")
        popup.lift()
        popup.attributes('-topmost', True)

        label = Label(popup, text="Filename:", anchor=W)
        label.pack(fill='x')

        filenameInputText = Entry(popup)
        filenameInputText.pack(fill='x')

        def saveOutputFile():
            if filenameInputText.get() == "":
                self.out_filename = "default"
            else:
                self.out_filename = filenameInputText.get()
            self.createTestScript()
            popup.destroy()

        def saveAndRun():
            if filenameInputText.get() == "":
                self.out_filename = "default"
            else:
                self.out_filename = filenameInputText.get()
            self.createTestScript()
            # self.createGherkinTest()
            self.permissionAndRun()
            popup.destroy()

        saveButton = Button(popup, text="CREATE PYTHON TEST", command=saveOutputFile)
        saveButton.pack(fill='x')

        saveAndRunButton = Button(popup, text="CREATE TESTS AND RUN", command=saveAndRun)
        saveAndRunButton.pack(fill='x')

    def createTestScript(self):

        self.writeHeader()
        self.generateTestFromEvents()
        self.writeFooter()

    def createGherkinTest(self):
        self.writeGherkinHeader()
        self.generateGherkinTestFromEvents()

    def createButtons(self):

        guiButton = Button(self.window,
                           highlightbackground="#32a852",
                           text="OPEN CULEBRA",
                           command=self.openCulebraGUI)
        guiButton.grid(column=35, row=0, columnspan=15, sticky=EW)

        givenButton = Button(self.window,
                             text="GIVEN",
                             command=self.moveToGivenArea,
                             highlightbackground="#ed4023")
        givenButton.grid(column=35, row=10, columnspan=15, sticky=EW)

        whenButton = Button(self.window,
                            text="WHEN",
                            command=self.moveToWhenArea,
                            highlightbackground="#033cf6")
        whenButton.grid(column=35, row=11, columnspan=15, sticky=EW)

        thenButton = Button(self.window,
                            text="THEN",
                            command=self.moveToThenArea,
                            highlightbackground="#fff952")
        thenButton.grid(column=35, row=12, columnspan=15, sticky=EW)

        upButton = Button(self.window, text="UP", command=self.moveUp)
        upButton.grid(column=35, row=5, columnspan=5, sticky=EW)

        downButton = Button(self.window, text="DOWN", command=self.moveDown)
        downButton.grid(column=40, row=5, columnspan=5, sticky=EW)

        removeButton = Button(self.window,
                              text="REMOVE",
                              command=self.removeElement)
        removeButton.grid(column=45, row=5, columnspan=5, sticky=EW)

        parametrizeButton = Button(self.window,
                              text="PARAMETRIZE",
                              command = self.parametrizeElement)
        parametrizeButton.grid(column=35, row=6, columnspan=15, sticky=EW)

        addTestArea = Button(self.window,
                              text="Add Test Area",
                             command = self.addTestAreaFunc)
        addTestArea.grid(column=35, row=8, columnspan=15, sticky=EW)

        runTestButton = Button(self.window,
                               text="SAVE TEST",
                               command=self.openSaveTestDialog)
        runTestButton.grid(column=35,
                           row=45,
                           rowspan=5,
                           columnspan=15,
                           sticky=NSEW)

    def showBDDDialog(self):
        with open('currentRecord.txt', 'r') as f:
            lines = f.read().splitlines()
            last_lines = lines[-3:-1]
            action = last_lines[0].strip(" ")
            code = last_lines[1].strip(" ")

        self.currentEvents.append({action: code})  # mali DONE
        self.updateCurrentEventsList()

    def addTestAreaFunc(self):  #caner
        
        bddInfoLabel = None
        selectedItemsFromCurrentEvents = self.currentEventsList.curselection()
        # selectedItemsFromLibrary = self.databaseEventsList.curselection()

        if selectedItemsFromCurrentEvents == ():
            return
        bddDialog = Toplevel()
        bddDialog.geometry('500x600+470+350')
        bddDialog.lift()
        bddDialog.attributes('-topmost', True)

        builded = False

        def on_closing():
            nonlocal builded
            builded = False
            self.actionTypeSet = 'Action'
            bddDialog.destroy()

        bddDialog.protocol('WM_DELETE_WINDOW', on_closing)

        v = StringVar(bddDialog, "1")

        def ShowChoice():
            self.actionTypeSet = v.get()
            bddInfoLabel['text'] = "GIVE YOUR (%s) ACTION A NAME" % self.actionTypeSet

        givenRadioButton = Radiobutton(bddDialog, text = 'Given', variable = v, command=ShowChoice, value = "Given", indicator = 0, background="#ed4023")
        givenRadioButton.pack(fill='x', ipady = 3)

        whenRadioButton = Radiobutton(bddDialog, text = 'When', variable = v, command=ShowChoice, value = "When", indicator = 0, background="#033cf6")
        whenRadioButton.pack(fill='x', ipady = 3)

        thenRadioButton = Radiobutton(bddDialog, text = 'Then', variable = v, command=ShowChoice, value = "Then", indicator = 0, background="#fff952")
        thenRadioButton.pack(fill='x', ipady = 3)

        bddInfoLabel = Label(bddDialog, text="GIVE YOUR (%s) ACTION A NAME" % self.actionTypeSet)
        bddInfoLabel.pack(fill='x')

        functionNameEntry = Entry(bddDialog)
        functionNameEntry.pack(fill='x')

        eventsLabel = []
        functionsEntry = []
        index = 0
        entriesText= []
        entriesTextIndex = []
        # bu kisimda indexing dogru degil maalesef. Düzeltilmesi gerek
        nonParametrizedWordCount = 0
        startingIndex = 0
        def callback():
            nonlocal entriesText, eventsLabel, entriesTextIndex, nonParametrizedWordCount, startingIndex
            index = -1
            for i in range(len(entriesTextIndex)):
                if entriesTextIndex[i] != entriesText[i].get():
                    index = i
                    entriesTextIndex[i] = entriesText[i].get()
                    break
            if index == -1:
                return
            quotesString = "'''"
            quoteString = "'"
            tirnakString = "\""
            oldLabelText = ""
            actionName = ""
            oldCodeText = ""
            for key in self.currentEvents[index+ nonParametrizedWordCount + startingIndex].keys():
                actionName = key
                oldCodeText = self.currentEvents[index+ nonParametrizedWordCount + startingIndex][key]
            findFirstIndex = actionName.find(quotesString)
            if findFirstIndex != -1:
                findSecondIndex = actionName.find(quotesString,findFirstIndex+len(quotesString))
                parametrizedWord = actionName[findFirstIndex + len(quotesString):findSecondIndex]
                newActionName = actionName.replace("'''" + parametrizedWord + "'''" ,"'''" + entriesText[index].get() + "'''")
                oldCodeText = oldCodeText.replace("'''" + parametrizedWord + "'''" ,"'''" + entriesText[index].get() + "'''")
            else:
                findFirstIndex = actionName.find(tirnakString)
                if findFirstIndex != -1:
                    findSecondIndex = actionName.find(tirnakString,findFirstIndex+len(tirnakString))
                    parametrizedWord = actionName[findFirstIndex + len(tirnakString):findSecondIndex]
                    newActionName = actionName.replace("\"" + parametrizedWord + "\"" ,"\"" + entriesText[index].get() + "\"")
                    oldCodeText = oldCodeText.replace("\"" + parametrizedWord + "\"" ,"\"" + entriesText[index].get() + "\"")
                else:
                    findFirstIndex = actionName.find(quoteString)
                    findSecondIndex = actionName.find(quoteString,findFirstIndex+len(quoteString))
                    parametrizedWord = actionName[findFirstIndex + len(quoteString):findSecondIndex]
                    newActionName = actionName.replace("'" + parametrizedWord + "'" ,"'" + entriesText[index].get() + "'")
                    oldCodeText = oldCodeText.replace("'" + parametrizedWord + "'" ,"'" + entriesText[index].get() + "'")
            self.currentEvents[index+ nonParametrizedWordCount + startingIndex][newActionName] = oldCodeText
            nonlocal builded
            if builded != False:
                del self.currentEvents[index+ nonParametrizedWordCount + startingIndex][actionName]
            eventsLabel[index]['text'] = newActionName
            self.updateCurrentEventsList()
            return True

        check = True
        for num, index in enumerate(selectedItemsFromCurrentEvents):
            if check == True:
                check = False
                startingIndex = index
            print('num', num)
            print('index', index)
            for key in self.currentEvents[index].keys():
                quotesString = "'''"
                quoteString = "'"
                tirnakString = "\""
                LabelText = key
                parametrizedWord = ""
                findFirstIndex = LabelText.find(quotesString)
                if findFirstIndex != -1:
                    findSecondIndex = LabelText.find(quotesString,findFirstIndex+len(quotesString))
                    parametrizedWord = LabelText[findFirstIndex + len(quotesString):findSecondIndex]
                else:
                    findFirstIndex = LabelText.find(tirnakString)
                    if findFirstIndex != -1:
                        findSecondIndex = LabelText.find(tirnakString,findFirstIndex+len(tirnakString))
                        parametrizedWord = LabelText[findFirstIndex + len(tirnakString):findSecondIndex]
                    else:
                        findFirstIndex = LabelText.find(quoteString)
                        if findFirstIndex != -1:
                            findSecondIndex = LabelText.find(quoteString,findFirstIndex+len(quoteString))
                            parametrizedWord = LabelText[findFirstIndex + len(quoteString):findSecondIndex]
                        else:
                            print('Entered')
                            nonParametrizedWordCount += 1
                            continue
                print("index-nonParametrizedWordCount",index-nonParametrizedWordCount-startingIndex)
                eventsLabel.append(Label(bddDialog, text=LabelText))
                eventsLabel[index-nonParametrizedWordCount-startingIndex].pack(fill='x')
                entriesText.append(StringVar())
                entriesText[index-nonParametrizedWordCount-startingIndex].trace("w", lambda name, index, mode, sv=entriesText[index-nonParametrizedWordCount-startingIndex]: callback())
                entriesText[index-nonParametrizedWordCount-startingIndex].set(parametrizedWord)
                entriesTextIndex.append(parametrizedWord)
                functionsEntry.append(Entry(bddDialog, textvariable=entriesText[index-nonParametrizedWordCount-startingIndex]))
                functionsEntry[index-nonParametrizedWordCount-startingIndex].pack(fill='x')
                # index += 1
                # indexTrack += 1
        builded = True
        errorLabelAction = Label(bddDialog, text="Please select given, when or then", background="red")
        errorLabel = Label(bddDialog, text="Please take ' paranthesis your parametrized words", background="red")
        errorLabelAction.destroy()
        errorLabel.destroy()
        def saveOutputFile():

            if self.actionTypeSet == 'Action':
                nonlocal errorLabelAction
                if errorLabelAction.winfo_exists() == 0:
                    errorLabelAction = Label(bddDialog, text="Please select given, when or then", background="red")
                    errorLabelAction.pack(fill='x')
                    errorLabelAction.after(5000, lambda: errorLabelAction.destroy())
            else:
                if (len(selectedItemsFromCurrentEvents) - nonParametrizedWordCount)*2 !=  functionNameEntry.get().count("'"):
                    nonlocal errorLabel
                    if errorLabel.winfo_exists() == 0:
                        errorLabel = Label(bddDialog, text="Please take ' paranthesis your parametrized words", background="red")
                        errorLabel.pack(fill='x')
                        errorLabel.after(5000, lambda: errorLabel.destroy())
                else:
                    tempCodes = {}
                    for num, index in enumerate(selectedItemsFromCurrentEvents):
                        for key in self.currentEvents[index].keys():
                            tempCodes.update({num: self.currentEvents[index][key]})

                    tempAction = {
                        "action_name": functionNameEntry.get(),
                        "action_type": self.actionTypeSet,
                        "codes": tempCodes
                    }

                    self.database.update({"%s" % str(len(self.database.keys())): tempAction})
                    self.updateDatabaseEventsList()

                    # for event in reversed(selectedItemsFromCurrentEvents):
                    #     self.currentEvents.remove(self.currentEvents[event])
                    #     self.currentEventsList.delete(event)

                    if self.actionTypeSet == "Given":
                        self.givenList.insert(END, functionNameEntry.get())

                    if self.actionTypeSet == "When":
                        self.whenList.insert(END, functionNameEntry.get())

                    if self.actionTypeSet == "Then":
                        self.thenList.insert(END, functionNameEntry.get())

                    # if selectedItemsFromLibrary != () and self.actionTypeSet == 'Given':
                    #     for selectedItem in selectedItemsFromLibrary:
                    #         self.givenList.insert(END, self.database[str(selectedItem)]['action_name'])
                    # if selectedItemsFromLibrary != () and self.actionTypeSet == 'When':
                    #     for selectedItem in selectedItemsFromLibrary:
                    #         self.whenList.insert(END, self.database[str(selectedItem)]['action_name'])
                    # if selectedItemsFromLibrary != () and self.actionTypeSet == 'Then':
                    #     for selectedItem in selectedItemsFromLibrary:
                    #         self.thenList.insert(END, self.database[str(selectedItem)]['action_name'])

                    self.databaseChanged = True
                    bddDialog.destroy()

        def cancelAction():
            bddDialog.destroy()

        closeButton = Button(bddDialog, text="CLOSE", command=cancelAction)
        closeButton.pack(fill='x')

        saveButton = Button(bddDialog, text="SAVE", command=saveOutputFile)
        saveButton.pack(fill='x')


    def showSaveActionDialog(self, actionType):
 
        bddDialog = Toplevel()
        bddDialog.geometry('500x100+470+350')
        bddDialog.lift()
        bddDialog.attributes('-topmost', True)

        bddInfoLabel = Label(bddDialog, text="GIVE YOUR (%s) ACTION A NAME" % actionType)
        bddInfoLabel.pack(fill='x')

        functionNameEntry = Entry(bddDialog)
        functionNameEntry.pack(fill='x')

        tempCurrentEvents = self.currentEventsList.curselection()

        def saveOutputFile():
            
            tempCodes = {}

            for num, index in enumerate(tempCurrentEvents):
                for key in self.currentEvents[index].keys():
                    tempCodes.update({num: self.currentEvents[index][key]})

            tempAction = {
                "action_name": functionNameEntry.get(),
                "action_type": actionType,
                "codes": tempCodes
            }

            self.database.update({"%s" % str(len(self.database.keys())): tempAction})
            self.updateDatabaseEventsList()

            for event in reversed(tempCurrentEvents):
                self.currentEventsList.delete(event)

            if actionType == "Given":
                self.givenList.insert(END, functionNameEntry.get())

            if actionType == "When":
                self.whenList.insert(END, functionNameEntry.get())

            if actionType == "Then":
                self.thenList.insert(END, functionNameEntry.get())

            self.databaseChanged = True
            bddDialog.destroy()

        def cancelAction():
            bddDialog.destroy()

        closeButton = Button(bddDialog, text="CLOSE", command=cancelAction)
        closeButton.pack(fill='x')

        saveButton = Button(bddDialog, text="SAVE", command=saveOutputFile)
        saveButton.pack(fill='x')

    def callBDDDialog(self):
        self.queue = queue.Queue()
        ThreadedTask(self.queue).start()
        self.window.after(100, self.process_queue)

    def process_queue(self):
        try:
            msg = self.queue.get(0)
            # Show result of the task if needed
            self.showBDDDialog()
        except queue.Empty:
            self.window.after(100, self.process_queue)

    def onQuitWindow(self):

        if self.databaseChanged:

            quitWindow = Toplevel()
            quitWindow.geometry('500x130+470+375')
            quitWindow.lift()
            quitWindow.attributes('-topmost', True)

            quitLabel = Label(quitWindow, text="WOULD YOU LIKE TO SAVE EVENTS TO DATABASE?",
                              background="yellow")
            quitLabel.pack(fill='x')

            closeButton = Button(quitWindow,
                                 text="CLOSE",
                                 command=quitLabel.destroy)
            closeButton.pack(fill='x')

            def saveToDatabase():
                with open("database.json", "w") as fp:
                    json.dump(self.database, fp, indent=2)
                quitWindow.destroy()
                sys.exit()

            saveButton = Button(quitWindow, text="SAVE", command=saveToDatabase)
            saveButton.pack(fill='x')
        else:
            sys.exit()

    def permissionAndRun(self):
        os.system("chmod +x %s.py && ./%s.py" % (self.out_filename, self.out_filename))


class AutocompleteEntry(Entry):
    def __init__(self, autocompleteList, *args, **kwargs):

        # Listbox length
        if 'listboxLength' in kwargs:
            self.listboxLength = kwargs['listboxLength']
            del kwargs['listboxLength']
        else:
            self.listboxLength = 8

        # Custom matches function
        if 'matchesFunction' in kwargs:
            self.matchesFunction = kwargs['matchesFunction']
            del kwargs['matchesFunction']
        else:
            def matches(fieldValue, acListEntry):
                pattern = re.compile('.*' + re.escape(fieldValue) + '.*', re.IGNORECASE)
                return re.match(pattern, acListEntry)

            self.matchesFunction = matches

        Entry.__init__(self, *args, **kwargs)
        self.focus()

        self.autocompleteList = autocompleteList

        self.var = self["textvariable"]
        if self.var == '':
            self.var = self["textvariable"] = StringVar()

        # self.bind_class('???', '<Key>',self.add_char)
        self.bind('<KeyPress>', self.add_char)

        self.var.trace('w', self.changed)
        self.bind("<Tab>", self.selection)

        self.listboxUp = False

    def add_char(self, evt):
        if evt.char != '\uf701' and evt.char != '\uf700':
            self.xview_moveto(1)
        if evt.char == '\uf701':  # down
            self.moveDown(evt)
            return 'break'
        if evt.char == '\uf700':  # up
            self.moveUp(evt)
            return 'break'

    def changed(self, name, index, mode):
        if self.var.get() == '':
            if self.listboxUp:
                self.listbox.destroy()
                self.listboxUp = False
        else:
            words = self.comparison()
            if words:
                if not self.listboxUp:
                    self.listbox = Listbox(width=self["width"], height=self.listboxLength)
                    self.listbox.bind("<Button-1>", self.selection)
                    self.listbox.bind("<Right>", self.selection)
                    self.listbox.place(x=self.winfo_x() + 30, y=self.winfo_y() + 30 + self.winfo_height())
                    self.listboxUp = True

                self.listbox.delete(0, END)
                for w in words:
                    self.listbox.insert(END, w)
            else:
                if self.listboxUp:
                    self.listbox.destroy()
                    self.listboxUp = False

    def selection(self, event):
        if self.listboxUp:
            temp = self.var.get()

            actionWord = temp[0:temp.find(" ") + 1]
            actionWord += self.listbox.get(ACTIVE)

            self.var.set(actionWord)
            self.listbox.destroy()
            self.listboxUp = False
            self.icursor(END)

    def moveUp(self, event):
        if self.listboxUp:
            if self.listbox.curselection() == ():
                index = '0'
            else:
                index = self.listbox.curselection()[0]

            if index != '0':
                self.listbox.selection_clear(first=index)
                index = str(int(index) - 1)

                self.listbox.see(index)  # Scroll!
                self.listbox.selection_set(first=index)
                self.listbox.activate(index)

    def moveDown(self, event):
        if self.listboxUp:
            if self.listbox.curselection() == ():
                index = '0'
            else:
                index = self.listbox.curselection()[0]

            if index != END:
                self.listbox.selection_clear(first=index)
                index = str(int(index) + 1)

                self.listbox.see(index)  # Scroll!
                self.listbox.selection_set(first=index)
                self.listbox.activate(index)

    def comparison(self):

        inputWord = self.var.get()
        hasGivenWord = inputWord.find("Given ") >= 0
        hasWhenWord = inputWord.find("When ") >= 0
        hasThenWord = inputWord.find("Then ") >= 0
        hasAndWord = inputWord.find("And ") >= 0

        if hasGivenWord or hasWhenWord or hasThenWord or hasAndWord:

            tempList = []
            if hasGivenWord:
                if isinstance(self.autocompleteList, dict):
                    for key in self.autocompleteList:
                        if self.autocompleteList[key]['action_type'] == 'Given':
                            tempList.append(self.autocompleteList[key]['action_name'])

                self.config(fg="red")

            if hasWhenWord:
                if isinstance(self.autocompleteList, dict):
                    for key in self.autocompleteList:
                        if self.autocompleteList[key]['action_type'] == 'When':
                            tempList.append(self.autocompleteList[key]['action_name'])

                self.config(fg="blue")

            if hasThenWord:
                if isinstance(self.autocompleteList, dict):
                    for key in self.autocompleteList:
                        if self.autocompleteList[key]['action_type'] == 'Then':
                            tempList.append(self.autocompleteList[key]['action_name'])

                self.config(fg="orange")

            searchWord = inputWord[inputWord.find(" ") + 1:]

            return [w for w in tempList if self.matchesFunction(searchWord, w)]
        else:
            return []


if __name__ == "__main__":

    root = Tk()
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)
    root.title("Capture and Replay")
    root.geometry('800x600+640+0')

    app = CaptureAndReplay(root)

    root.protocol('WM_DELETE_WINDOW', app.onQuitWindow)

    root.mainloop()

    app.observer.join()