import json, re, sys
import webbrowser
import tkinter as tk
import tkinter.ttk as ttk
import customtkinter as ctk
from util.database import Database
from util.logger import Logger
from util.mail import Mail
from util.basedir import BaseDir
from util.user import User
from util.popup import PopUp
from html.parser import HTMLParser

# disable certificate warnings
import urllib3
urllib3.disable_warnings()

if len(sys.argv) < 1:
    print("invalid usage, use like this: \npython service.py [config.json]")
    sys.exit(1)

ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.data = []
        self.capture = False

    def handle_starttag(self, tag, attrs):
        if tag in ('p', 'h1'):
            self.capture = True

    def handle_endtag(self, tag):
        if tag in ('p', 'h1'):
            self.capture = False

    def handle_data(self, data):
        if self.capture:
            self.data.append(data)

class ScrollableCheckBoxFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, item_list, command=None, **kwargs):
        super().__init__(master, **kwargs)

        self.command = command
        self.checkbox_list = []
        for i, item in enumerate(item_list):
            self.add_item(item)

    def add_item(self, item):
        checkbox = ctk.CTkCheckBox(self, text=item)
        if self.command is not None:
            checkbox.configure(command=self.command)
        checkbox.grid(row=len(self.checkbox_list), column=0, pady=10, padx=10, sticky="nw")
        self.checkbox_list.append(checkbox)

    def remove_item(self, item):
        for checkbox in self.checkbox_list:
            if item == checkbox.cget("text"):
                checkbox.destroy()
                self.checkbox_list.remove(checkbox)
                return

    def get_checked_items(self):
        return [checkbox.cget("text") for checkbox in self.checkbox_list if checkbox.get() == 1]
    
    def changeselectall(self, action):
        if action == 0:
            for checkbox in self.checkbox_list:
                checkbox.deselect()
        else:
            for checkbox in self.checkbox_list:
                checkbox.select()
        
    def changestate(self, action):
        if action == 0:
            for checkbox in self.checkbox_list:
                checkbox.configure(state="disabled")
        else:
            for checkbox in self.checkbox_list:
                checkbox.configure(state="normal")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # load config
        self.config = json.loads(open(sys.argv[1], "r").read())
        self.notify = PopUp(self.config)
        self.mail = Mail(self.config)

        # load logger
        self.logger = Logger().getLogger("Application")

        # connect to database
        self.db = Database(self.config["database"]["driver"], self.config["database"]["host"], self.config["database"]["database"], self.config["database"]["owner"])
        # configure window
        self.title("Notification Manager")
        self.geometry(f"{1100}x{580}")
        self.iconbitmap(BaseDir.get() + '\\ico\\' + 'notification-manager.ico')
        # configure grid layout (1x2) (rowsxcollumns)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0) # collumns 0 and 1 should be fixed
        self.grid_columnconfigure(1, weight=1) 
        
        
        # create sidebar frame with widgets
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=7, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.button_start = ctk.CTkButton(self.sidebar_frame, text="Raise notification", command=self.event_button_start)
        self.button_start.grid(row=1, column=0, padx=20, pady=10)
        self.button_stop = ctk.CTkButton(self.sidebar_frame, text="Solve notification", command=self.event_button_stop)
        self.button_stop.grid(row=2, column=0, padx=20, pady=10)
        self.sep = ttk.Separator(self.sidebar_frame)
        self.sep.grid(row=3, column=0, padx=20, pady=20, sticky="ew")
        self.label_std_texts = ctk.CTkLabel(self.sidebar_frame, text="Standard Texts:")
        self.label_std_texts.grid(row=4, column=0, padx=20, pady=(10, 0), sticky="n")
        self.optionemenu_std_texts = ctk.CTkOptionMenu(self.sidebar_frame, values=["None"], command=self.event_change_std_texts)
        self.optionemenu_std_texts.grid(row=5, column=0, padx=20, pady=(10, 0), sticky="n")     
        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"], command=self.event_change_appearance_mode)
        self.appearance_mode_optionemenu.grid(row=7, column=0, padx=20, pady=(10, 10))
        self.scaling_label = ctk.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=8, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["80%", "90%", "100%", "110%", "120%"], command=self.event_change_scaling)
        self.scaling_optionemenu.grid(row=9, column=0, padx=20, pady=(10, 20))
        self.button_help = ctk.CTkButton(self.sidebar_frame, text="Help", command=self.event_button_help)
        self.button_help.grid(row=10, column=0, padx=20, pady=10)
        
        # create tabview
        self.tabview = ctk.CTkTabview(self, width=250)
        self.tabview.grid(row=0, column=1, padx=(20, 0), pady=(20, 0), sticky="nsew")
        self.tabview.add("Notification")
        self.tabview.add("User Selection")
        # configure grid of individual tabs
        self.tabview._segmented_button.grid(sticky="w") 
        self.tabview.tab("Notification").grid_rowconfigure((0, 1, 2), weight=0) # rows 0, 1 and 2 should be fixed
        self.tabview.tab("Notification").grid_rowconfigure(3, weight=1)
        self.tabview.tab("Notification").grid_columnconfigure((0, 1), weight=0) # collumns 0 and 1 should be fixed 
        self.tabview.tab("Notification").grid_columnconfigure(2, weight=1) 
        self.tabview.tab("User Selection").grid_rowconfigure(0, weight=0) # rows 0 should be fixed
        self.tabview.tab("User Selection").grid_rowconfigure(1, weight=1)
        self.tabview.tab("User Selection").grid_columnconfigure((0, 1), weight=1)
        
        # create frame and combobox level
        self.frame_level = ctk.CTkFrame(self.tabview.tab("Notification"))
        self.frame_level.grid(row=1, column=2, columnspan=2, padx=20, pady=10, sticky="nsew")   
        self.combobox_level = ctk.CTkComboBox(master=self.frame_level, values=["", "1", "2", "3"], width=75, command=self.event_change_level)
        self.combobox_level.grid(row=0, column=0, padx=20, pady=10, sticky="nsw")
        
        # create entry
        self.shorttext = ctk.CTkEntry(self.tabview.tab("Notification"))
        self.shorttext.grid(row=2, column=2, columnspan=2, padx=20, pady=20, sticky="nsew")
        
        # create textbox
        self.longtext = ctk.CTkTextbox(self.tabview.tab("Notification"))
        self.longtext.grid(row=3, column=2, columnspan=2, padx=20, pady=20, sticky="nsew")
        
        # set default values
        self.appearance_mode_optionemenu.set("Dark")
        self.scaling_optionemenu.set("100%")
        self.combobox_level.set("")
        strStatus = self.event_update_status()
        self.radio_var = tk.IntVar(value=0)
        
        # create labels
        self.label_status1 = ctk.CTkLabel(self.tabview.tab("Notification"), text="Status:")
        self.label_status1.grid(row=0, column=1, padx=20, pady=20, sticky="nse")
        self.label_status2 = ctk.CTkLabel(self.tabview.tab("Notification"), text=strStatus)
        self.label_status2.grid(row=0, column=2, padx=20, pady=20, sticky="w")
        self.label_level = ctk.CTkLabel(self.tabview.tab("Notification"), text="Level:")
        self.label_level.grid(row=1, column=1, padx=20, pady=20, sticky="nse")
        self.label_level2 = ctk.CTkLabel(master=self.frame_level, text="")
        self.label_level2.grid(row=0, column=2, padx=20, pady=10, sticky="nsw")
        self.label_shorttext = ctk.CTkLabel(self.tabview.tab("Notification"), text="Title:")
        self.label_shorttext.grid(row=2, column=1, padx=20, pady=20, sticky="nse")
        self.label_longtext = ctk.CTkLabel(self.tabview.tab("Notification"), text="Description:")
        self.label_longtext.grid(row=3, column=1, padx=20, pady=20, sticky="ne")
        
        # create radiobutton frame
        self.radiobutton_frame = ctk.CTkFrame(self.tabview.tab("User Selection"))
        self.radiobutton_frame.grid(row=0, column=0, columnspan=4, padx=(20, 20), pady=(20, 0), sticky="nsew")
        self.radiobutton_frame.grid_columnconfigure((0,1,2), weight=0)
        self.radiobutton_frame.grid_columnconfigure((3,4), weight=1)
        self.label_radiogroup = ctk.CTkLabel(master=self.radiobutton_frame, text="Choose a user group:")
        self.label_radiogroup.grid(row=0, column=0, padx=10, pady=10, sticky="nse")
        self.radiobutton_1 = ctk.CTkRadioButton(master=self.radiobutton_frame, command=self.event_radiobutton, variable=self.radio_var, value=0, text="Active users now")
        self.radiobutton_1.grid(row=0, column=1, pady=10, padx=20, sticky="ns")
        self.radiobutton_2 = ctk.CTkRadioButton(master=self.radiobutton_frame, command=self.event_radiobutton, variable=self.radio_var, value=1, text="Active users last 90 days")
        self.radiobutton_2.grid(row=0, column=2, pady=10, padx=20, sticky="ns")
        self.checkbox_selectall = ctk.CTkCheckBox(master=self.radiobutton_frame, command=self.event_selectall, text="Select All")
        self.checkbox_selectall.grid(row=0, column=3, pady=20, padx=20, sticky="nse")

        # get current active users in Application
        actU = self.db.getCurrentActiveUsers()
        actU_clean = []
        [actU_clean.append(u) for u in actU if u not in actU_clean]
        actUsersNow = []
        for user in actU_clean:
            if user[3] != None:
                actUsersNow.append("%s, %s <%s>" % (user[1], user[2], user[3]))
                
        # get current active users in Application
        actU90d = self.db.getActiveUsersLast90Days()
        actU90d_clean = []
        [actU90d_clean.append(u) for u in actU90d if u not in actU90d_clean]
        actUsers90days = []
        for user in actU90d_clean:
            if user[2] != None:
                actUsers90days.append("%s, %s <%s>" % (user[0], user[1], user[2]))
        
        # create scrollable checkbox frames
        self.scrollable_checkbox_frame1 = ScrollableCheckBoxFrame(master=self.tabview.tab("User Selection"), item_list=actUsersNow)
        self.scrollable_checkbox_frame1.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")
        # create scrollable checkbox frames
        self.scrollable_checkbox_frame2 = ScrollableCheckBoxFrame(master=self.tabview.tab("User Selection"), item_list=actUsers90days)
        self.scrollable_checkbox_frame2.grid(row=1, column=1, padx=15, pady=15, sticky="nsew")
        self.scrollable_checkbox_frame1.changeselectall(1)
        self.event_radiobutton()
        
        # read txt files
        self.short_bugfixing = open(BaseDir.get() + '\\txt\\' + 'short-bugfixing.txt','r').readline()
        self.short_downtime = open(BaseDir.get() + '\\txt\\' + 'short-downtime.txt','r').readline()
        self.short_infrastructure = open(BaseDir.get() + '\\txt\\' + 'short-infrastructure.txt','r').readline()
        self.short_performance = open(BaseDir.get() + '\\txt\\' + 'short-performance.txt','r').readline()
        
        # read html files
        parser_bugfixing = Parser()
        parser_bugfixing.feed(open(BaseDir.get() + '\\html\\' + 'message-bugfixing.html','r').readline())
        self.message_bugfixing = parser_bugfixing.data
        parser_downtime = Parser()
        parser_downtime.feed(open(BaseDir.get() + '\\html\\' + 'message-downtime.html','r').readline())
        self.message_downtime = parser_downtime.data
        parser_infra = Parser()
        parser_infra.feed(open(BaseDir.get() + '\\html\\' + 'message-infrastructure.html','r').readline())
        self.message_infrastructure = parser_infra.data
        parser_performance = Parser()
        parser_performance.feed(open(BaseDir.get() + '\\html\\' + 'message-performance.html','r').readline())
        self.message_performance = parser_performance.data
        parser_solve = Parser()
        parser_solve.feed(open(BaseDir.get() + '\\html\\' + 'message-solve.html','r').readline())
        self.message_solve = parser_solve.data
    
    def event_change_appearance_mode(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
    
    def event_change_scaling(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        ctk.set_widget_scaling(new_scaling_float)
    
    def event_radiobutton(self):
        if self.radio_var.get() == 0:
            self.scrollable_checkbox_frame2.changestate(0)
            self.scrollable_checkbox_frame1.changestate(1)
        else:
            self.scrollable_checkbox_frame1.changestate(0)
            self.scrollable_checkbox_frame2.changestate(1)
            
    def event_selectall(self):
        if self.radio_var.get() == 0:
            if self.checkbox_selectall.get() == 0:
                self.scrollable_checkbox_frame1.changeselectall(0)
            else:
                self.scrollable_checkbox_frame1.changeselectall(1)
        else:
            if self.checkbox_selectall.get() == 0:
                self.scrollable_checkbox_frame2.changeselectall(0)
            else:
                self.scrollable_checkbox_frame2.changeselectall(1)
    
    def event_change_level(self, new_level: str):
        if new_level == "1":
            self.label_level2.configure(text="Users will receive an email notification, new system notification will be created without showing pop-up.")
        elif new_level == "2":
            self.label_level2.configure(text="Users will receive an email notification + pop-up message on their screen.")
        elif new_level == "3":
            self.label_level2.configure(text="Users will receive an email notification + pop-up message on their screeen, and Application Edit Mode will be locked.")
        else:
            self.label_level2.configure(text="")
    
    def event_update_status(self):
        actNot = self.notify.checkActiveNotifications()
        if actNot > 0:
            self.button_start.configure(state="disabled")
            self.button_stop.configure(state="normal")
            self.combobox_level.configure(state="disabled")
            self.optionemenu_std_texts.configure(values=["None", "Solve"])
            self.usrNot = self.notify.checkNotifiedUsers()
            return "There is/are " + str(actNot) + " activated notifications. Click Stop before starting a new one!"
        else:
            self.button_start.configure(state="normal")
            self.button_stop.configure(state="disabled")
            self.combobox_level.configure(state="normal")
            self.optionemenu_std_texts.configure(values=["None", "Bugfixing", "Downtime", "Infrastructure", "Performance"])
            return "No active notifications!"
    
    def event_button_start(self):
        level = self.combobox_level.get()
        shortText = self.shorttext.get()
        longText = self.longtext.get("0.0", "end")
        if level and shortText and longText:
            adresses = []
            usersIDs = []
            if self.radio_var.get() == 0:
                users = self.scrollable_checkbox_frame1.get_checked_items()
            else:
                users = self.scrollable_checkbox_frame2.get_checked_items()
            for user in users:
                adresses.append(re.search('<(.*?)>', user).group(1))
            if users:
                blnConfirm = 1
                for userID in self.db.getUserIDs(adresses):
                    usersIDs.append(userID[0])
            else:
                blnConfirm = tk.messagebox.askyesno("Question", "No user has been chosen in the selection tab.\nDo you still want to continue creating the notification?")

            if blnConfirm:
                if len(adresses) != 0:
                    # send email notification
                    if self.mail.sendMail(adresses, shortText, longText):
                        tk.messagebox.showinfo("Info", "Email notification successfully sent!")
                    else:
                        tk.messagebox.showerror(None, "Error sending email notification.")
                else:
                    tk.messagebox.showinfo("Info", "No user is active on the system.\nNotification email did not need to be sent.")
    
                # create system notification
                user = User.get() # get logged user
                if self.notify.createNotification(user[0], user[1], level, shortText, longText, '1','0','0', usersIDs):
                    tk.messagebox.showinfo("Info", "System notification successfully created!")
                else:
                    tk.messagebox.showerror(None, "Error creating system notification.")
    
                self.combobox_level.set("")
                self.label_level2.configure(text="")
                self.optionemenu_std_texts.set("None")
                self.shorttext.delete(0,len(self.shorttext.get()))
                self.longtext.delete(0.0, tk.END)    
                strStatus = self.event_update_status()
                self.label_status2.configure(text=strStatus)
            else:
                self.tabview.set("User Selection")  # change focus to User Selection tab
        else:
            tk.messagebox.showinfo("Info", "You must choose a level and write the title and description to start a notification.")
            
    def event_button_stop(self):
        shortText = self.shorttext.get()
        longText = self.longtext.get("0.0", "end")
        if shortText and longText:
            adrNot = []
            diffAdr = []
            usersIDs = []
            adresses = []
            if self.radio_var.get() == 0:
                users = self.scrollable_checkbox_frame1.get_checked_items()
            else:
                users = self.scrollable_checkbox_frame2.get_checked_items()
            for user in users:
                adresses.append(re.search('<(.*?)>', user).group(1))
            
            for email in self.db.getNotifiedUsersEmails(list(self.usrNot[3].split(','))):
                adrNot.append(email[0])
            [diffAdr.append(a) for a in adresses if a not in adrNot]
            if diffAdr:
                if tk.messagebox.askyesno("Question", "There are new users who were not notified in the last notification.\nDo you want to include them in the solution notification?"):
                    adrNot.extend(diffAdr) 
            if adrNot:
                for userID in self.db.getUserIDs(adrNot):
                    usersIDs.append(userID[0])
                
            if self.notify.desactivateNotifications(usersIDs):        
                if len(adrNot) != 0:
                    # send email notification
                    if self.mail.sendMail(adrNot, shortText, longText):
                        tk.messagebox.showinfo("Info", "Email notification successfully sent!")
                    else:
                        tk.messagebox.showerror(None, "Error sending email notification.")
                else:
                    tk.messagebox.showinfo("Info", "No user has been notified previously.\nNotification email did not need to be sent.")
                self.optionemenu_std_texts.set("None")
                self.shorttext.delete(0,len(self.shorttext.get()))
                self.longtext.delete(0.0, tk.END) 
                strStatus = self.event_update_status()
                self.label_status2.configure(text=strStatus)
                tk.messagebox.showinfo("Info", "Notifications successfully deactivated!")
            else:
                tk.messagebox.showerror(None, "Error in desactivating the notifications.")
        else:
            tk.messagebox.showinfo("Info", "You must write the title and description to stop a notification.")

    def event_change_std_texts(self, new_std_text: str):
        self.shorttext.delete(0,len(self.shorttext.get()))
        self.longtext.delete(0.0, tk.END)
        if new_std_text == "Bugfixing":
            self.shorttext.insert(0, self.short_bugfixing)
            insert_text = self.message_bugfixing
        elif new_std_text == "Downtime":
            self.shorttext.insert(0, self.short_downtime)
            insert_text = self.message_downtime
        elif new_std_text == "Infrastructure":
            self.shorttext.insert(0, self.short_infrastructure)
            insert_text = self.message_infrastructure
        elif new_std_text == "Performance":
            self.shorttext.insert(0, self.short_performance)
            insert_text = self.message_performance
        elif new_std_text == "Solve":
            self.shorttext.insert(0, "Solved: " + self.usrNot[2])
            insert_text = self.message_solve
        for line in insert_text:
            self.longtext.insert(tk.CURRENT, line + "\n")

    def event_button_help(self):
        webbrowser.open('XXXXXXXXXXX')  

    def on_closing(self):
        if tk.messagebox.askokcancel("Quit", "Do you want to quit?"):
            app.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()