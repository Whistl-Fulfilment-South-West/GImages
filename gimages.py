import sys
import os
import glob
from datetime import datetime
import pyodbc
from PIL import Image, ImageTk
import io
import logging
import time
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import time
import tkinter.font
#from tkinter import filedialog ##no longer used



class GImageApp:
    def __init__(self, master,maint):
        #splash screen remains open unless you call pyi_splash.close(), but pyi_splash is not available outside of a pyinstaller-compiled exe. Therefore need to do this silly thing to get it to close.
        try:
            import pyi_splash
            pyi_splash.close()
        except:
            pass
        #Initiate all the "global" variables 
        self.master = master
        self.master.title("GImages")
        self.source = None
        self.client = None
        self.sep = None
        self.maint = maint
        self.errorflag = 0
        self.font = tkinter.font.Font(family="Arial Rounded MT Bold", size=10)
        self.show_start_screen()
    
    def show_start_screen(self):
        #Make sure the master window does not show anywhere
        self.master.withdraw()
        #If this is not the maintenance shortcut, skip directly to the Display screen and do not allow them anywhere else
        if self.maint == 0:
            self.launch_maintenance(0)
            sys.exit()

        #choice dictionary to choose action once button pressed
        res = {'choice': None}

        #button actions
        def maint():
            res["choice"] = 'maint'
            start_window.destroy()

        def imp():
            res["choice"] = 'imp'
            start_window.destroy()

        def display():
            res["choice"] = "display"
            start_window.destroy()

        def folder():
            res["choice"] = "folder"
            start_window.destroy()

        #exiting/closing close entire app
        def exit_app():
            self.master.destroy()
        
        def on_close():
            self.master.destroy()

        #Initiate start screen
        start_window = tk.Toplevel()
        start_window.title("GImages")
        start_window.geometry("400x230")  

        start_window.protocol("WM_DELETE_WINDOW", on_close)
        
        message = tk.Label(start_window, text="Choose your action", wraplength=280, justify="left", font = self.font)
        message.pack(padx=10, pady=20)

        #Frame to contain the button "grid"
        button_frame = tk.Frame(start_window)
        button_frame.pack(pady=10)

        #Standard button width for GUI loveliness
        button_width = 15

        #Initialise buttons within frame, with actions as set above
        maint_button = tk.Button(button_frame, text="Maintenance", command=maint, width=button_width)
        maint_button.grid(row=0, column=0, padx=10)

        imp_button = tk.Button(button_frame, text="Import", command=imp, width=button_width)
        imp_button.grid(row=0, column=1, padx=10)

        disp_button = tk.Button(button_frame, text = "Display",command = display,width=button_width)
        disp_button.grid(row=1,column=0,padx=10,pady=10)

        fold_button = tk.Button(button_frame, text = "Create Folder",command = folder,width=button_width)
        fold_button.grid(row=1,column=1,padx=10,pady=10)
        
        #Exit button packed below button frame
        exit_button = tk.Button(start_window, text="Exit", command=exit_app, width=button_width)
        exit_button.pack(pady=5,padx=10)

        #Loop window until action chosen, then perform chosen action
        start_window.wait_window()
        if res["choice"] == 'maint':
            self.launch_maintenance(1)
        elif res["choice"] == 'imp':
            self.launch_import()
        elif res["choice"] == 'display':
            self.launch_maintenance(0)
        elif res["choice"] == "folder":
            self.folder_create()

    #Screen for just choosing the client (used in import and folder creation processes)
    def clientchoose(self):
        server = 'SQL-SSRS'
        database = 'Appz'
        try:
            # Connect to DB and fetch client data
            cnxn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes')
            cursor = cnxn.cursor()
            query = "SELECT clid, descr FROM clid WHERE descr IS NOT NULL"
            cursor.execute(query)

            # Create mappings
            descr_to_clid = {}
            descr_list = []
            for row in cursor.fetchall():
                clid, descr = row
                descr_to_clid[descr] = clid
                descr_list.append(descr)

            selected_value = {"value": None}

            #GUI actions
            def on_ok():
                selected_descr = combo.get()
                selected_value["value"] = descr_to_clid.get(selected_descr)
                main_window.destroy()

            def on_selection(event):
                ok_button.config(state="normal")
            #If you press an alphabetical key, dropdown menu will skip to the next client starting with that letter. Tab will also select the current client highlighted (activating ok button)
            def on_keypress(event):
                letter = event.char.lower()
                if event.keysym == "Tab" and combo.current() != -1:
                    on_selection()
                    return
                elif not letter.isalpha():
                    return
                current_index = combo.current()
                total_items = len(descr_list)
                for i in range(1, total_items + 1):
                    next_index = (current_index + i) % total_items
                    if descr_list[next_index].lower().startswith(letter):
                        combo.current(next_index)
                        break
            main_window = tk.Toplevel()
            main_window.title("Choose Client")
            main_window.geometry("350x150")
            #dropdown menu initialised with client list
            combo = ttk.Combobox(main_window, state="readonly", values=descr_list)
            combo.place(x=50, y=40)
            combo.bind("<<ComboboxSelected>>", on_selection)
            combo.bind("<Key>", on_keypress)
            #ok button initialised disabled until a client is selected
            ok_button = tk.Button(main_window, text="OK", state="disabled", command=on_ok)
            ok_button.place(x=130, y=90)

            main_window.wait_window()

            return selected_value["value"]
        
        except Exception as e:
            logging.error(f"Error: {e}", exc_info=True)
        return

    def folder_create(self):
        #get client, create folder based on clid returned
        client = self.clientchoose()
        folder = '//Elucid9/Elucid/Data_Import/Gimage/' + client
        if os.path.isdir(folder):
            messagebox.showinfo("GImages Folder", f"{folder} already exists")
        else:
            os.makedirs(folder,exist_ok=True)
            messagebox.showinfo("GImages Folder",f"Folder created - {folder}")
        self.show_start_screen()
    
    def sepchoose(self):
        separator_value = {"value": None}
        #Sepearator needs to be a single character. No other restrictions at a code level
        def on_key_release(event):
            text = entry.get()
            if len(text) == 1:
                ok_button.config(state="normal")
            else:
                ok_button.config(state="disabled")

        def on_ok():
            separator_value["value"] = entry.get()
            root.destroy()

        root = tk.Toplevel()
        root.title("Enter Separator")
        root.geometry("300x150")

        #Some text to guide users
        label = tk.Label(root, text="Enter a single character separator:", font = self.font)
        label.pack(pady=10)

        hint_label = tk.Label(root, text="If no separator used in your files,\n"
                                        "please enter a single digit not in your filenames.",
                            wraplength=280, justify="center", fg="gray")
        hint_label.pack(pady=(0, 10))

        entry = tk.Entry(root, width=5, justify="center")
        entry.pack()
        entry.bind("<KeyRelease>", on_key_release)

        #ok button disabled until single character entered entered
        ok_button = tk.Button(root, text="OK", command=on_ok, state="disabled")
        ok_button.pack(pady=10)

        root.wait_window()
        return separator_value["value"]
        
    def getino(self,client,part):
        #Connect to database
        server = 'SQL-SSRS'
        database = 'Appz'
        try:
            cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';Trusted_Connection=yes')
            cursor = cnxn.cursor()
            #GImage_getino gets max image number for client and part
            query = "EXEC GImage_getino ?,?"
            cursor.execute(query,(client,part))
            nuino = cursor.fetchone()
            #add one to this to get new image number
            return int(nuino[0]) + 1

        except Exception as e:
            logging.error(f"Error: {e}", exc_info = True)
        finally:
            #Close connections if they still exist
            if 'cursor' in locals():
                cursor.close()
            if 'cnxn' in locals():
                cnxn.close()

    #method to make sure part exists on database (for import)
    def check_part_exists(self,part,client):
        server = 'SQL-SSRS'
        database = 'Appz'
        try:
            # Connect to DB and fetch part data
            cnxn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes')
            cursor = cnxn.cursor()
            cursor.execute("EXEC GImage_PartCheck ?, ?", part, client)
            row = cursor.fetchone()
            #if we got anything, everything is fine yay
            if row:
                return 1
            else:
                # Part does not exist – show message box
                root = tk.Tk()
                root.withdraw()
                messagebox.showinfo("Part Not Found", f"Part {part} does not exist on {client}. Skipping.")
                root.destroy()
                #return 0 will cause import to be skipped
                return 0

        except Exception as e:
            logging.error(f"Error: {e}", exc_info=True)
            self.errorflag = 1
            return

        finally:
            #Close connections if they still exist
            if 'cursor' in locals():
                cursor.close()
            if 'cnxn' in locals():
                cnxn.close()

    #Method to update image if part/client/ino combo already exists and user wants it changed
    def updateimage(self,client, image, part, ino):
        
        server = 'SQL-SSRS'
        database = 'Appz'
        image_binary = convert_image_to_binary(image)
        try:
            cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';Trusted_Connection=yes')
            cursor = cnxn.cursor()
            query = """EXEC GImage_Update ?, ?, ?, ?"""
            cursor.execute(query,(client,image_binary,part,ino))
            cnxn.commit()
        except Exception as e:
            logging.error(f"Error: {e}", exc_info = True)
            self.errorflag = 1
        finally:
            #Close connections if they still exist
            if 'cursor' in locals():
                cursor.close()
            if 'cnxn' in locals():
                cnxn.close()   

    #Method to compare and choose between two images
    def choose_image_version(self,old_image_bytes, new_image_bytes, client, image, part, ino):
        result = {"choice": None}
        
        #Button actions
        def use_new():
            logging.info("Overwriting old image")
            self.updateimage(client, image, part, ino)
            result["choice"] = "Y"
            window.destroy()

        def keep_old():
            logging.info("Discarding new image")
            result["choice"] = "N"
            window.destroy()

        def add_new():
            logging.info("Adding image as new ino")
            nuino = self.getino(client,part)
            result["choice"] = "N"
            self.insertimage(client,image,part,nuino)
            window.destroy()

        # Convert binary to PhotoImage via PIL
        old_img = Image.open(io.BytesIO(old_image_bytes))
        new_img = Image.open(io.BytesIO(new_image_bytes))

        # Resize to fit window if needed
        max_size = (300, 300)
        old_img.thumbnail(max_size)
        new_img.thumbnail(max_size)


        # Setup tkinter window
        window = tk.Toplevel()
        window.title(f"Compare Images - {part}")

        #reference images
        old_photo = ImageTk.PhotoImage(old_img)
        new_photo = ImageTk.PhotoImage(new_img)

        #setup image frame
        image_frame = tk.Frame(window)
        image_frame.pack(padx=10, pady=10)
        
        #enter old image
        old_label = tk.Label(image_frame, text="Old Image\n", compound="top", font = self.font)
        old_label.image = old_photo  # Keep reference
        old_label.configure(image=old_photo)
        old_label.pack(side="left", padx=10)
        
        #enter new image
        new_label = tk.Label(image_frame, text="New Image\n", compound="top", font = self.font)
        new_label.image = new_photo
        new_label.configure(image=new_photo)
        new_label.pack(side="right", padx=10)
        
        #button frame
        btn_frame = tk.Frame(window)
        btn_frame.pack(pady=10)

        #"keep old image" button
        keep_old_btn = tk.Button(btn_frame, text="Keep Old Image", command=keep_old, width=20)
        keep_old_btn.grid(row=0, column=0, padx=10)

        #"use new image" button
        use_new_btn = tk.Button(btn_frame, text="Use New Image", command=use_new, width=20)
        use_new_btn.grid(row=0, column=1, padx=10)

        #add old image as new image (row below other two buttons, spanning both sides)
        add_new_btn = tk.Button(btn_frame, text="Add As New Image", command=add_new, width=42)
        add_new_btn.grid(row=1, column=0, columnspan=2, pady=(10, 0))

        # Let Tkinter auto-size the window
        window.wait_window()

        #Return the correct choice, if the user exits out, discard the new image (FUTURE CHECK ON BEHAIVOUR OF KEEPING IMAGE AS NEW IMAGE - LOOKS GOOD BUT NOT SURE WHY?)
        if result["choice"] == "Y":
            return 1
        elif result["choice"] == "N":
            return 0
        else:
            logging.info("No selection made. Discarding new image.")
            return 0
        
    #Method to insert new image into database (deduping already done, so should be no duplication problems(tm))
    def insertimage(self,client, image, part, ino):
        server = 'SQL-SSRS'
        database = 'Appz'
        image_binary = convert_image_to_binary(image)
        try:
            cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';Trusted_Connection=yes')
            cursor = cnxn.cursor()
            query = """EXEC GImage_Insert ?, ?, ?, ?"""
            cursor.execute(query,(client,image_binary,part,ino))
            cnxn.commit()
        except Exception as e:
            logging.error(f"Error: {e}", exc_info = True)
            self.errorflag = 1
        finally:
            #Close connections if they still exist
            if 'cursor' in locals():
                cursor.close()
            if 'cnxn' in locals():
                cnxn.close()
    
    #Method to move file to archive with datetimestamp added
    def archivefile(self,image,dest):
        suffix = os.path.splitext(image)[1]
        file = os.path.basename(image)
        ind = file.find(suffix)
        nufile = file[:ind] + datetime.now().strftime("%Y%m%dT%H%M%S") + file[ind:]
        os.rename(image, dest + "/" + nufile)

    def dedupe(self,client,image, part, ino):
        #returns 1 if duplicate found (and dedupe done one way or the other), 0 if not
        server = 'SQL-SSRS'
        database = 'Appz'
        try:
            #SQL to find if an image for that SKU, client and image number already exists
            cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';Trusted_Connection=yes;')
            cursor = cnxn.cursor()
            query = """EXEC GImage_dedupe ?, ?, ?"""
            cursor.execute(query, (part, client, ino))
            exists = cursor.fetchone()[0] > 0
            #if we found anything, go through dedupe process
            if exists:
                logging.warning("Part %s, image no %s already exists for %s", part, ino, client)
                #Get old image
                grabmage = """EXEC GImage_grabimage ?, ?, ?"""
                cursor.execute(grabmage, (part, client, ino))
                olimage = cursor.fetchone()[0]
                #convert new image into binary for display
                nuimage = convert_image_to_binary(image)
                logging.info("Requesting decision from user")
                #Bring up the image-choose screen with both images
                ans = self.choose_image_version(olimage,nuimage,client,image,part,ino)
                if ans == 1:
                    self.updateimage(client,image,part,ino)
                return 1
                
            else:
                return 0
            
        except Exception as e:
            logging.error(f"Error: {e}", exc_info = True)
            self.errorflag = 1

        finally:
            #Close connections if they still exist
            if 'cursor' in locals():
                cursor.close()
            if 'cnxn' in locals():
                cnxn.close()    
    
    #Method for the import process
    def launch_import(self):
        try:
            self.master.withdraw()
            client = self.clientchoose()
            sep = self.sepchoose()

            #If user exits client screen without choosing client/separator, show error and return to start screen
            if not client or not sep:
                self.err_display("Import failed - Please choose client and separator")
                self.client = None
                self.sep = None
                self.show_start_screen()
                sys.exit()
            
            #Set source folder based on clid
            if not self.source:
                self.source = '//Elucid9/Elucid/Data_Import/Gimage/' + client
                os.makedirs(self.source,exist_ok=True)
                messagebox.showinfo("GImages Source",f"Images will be downloaded from {self.source}")

            #Setup logging - set log destination
            log_dest = self.source + f"/logs"
            os.makedirs(log_dest,exist_ok=True)

            #Setup logging - create log file
            logfile = f"{log_dest}/log{datetime.now().strftime("%Y%m%dT%H%M%S")}.log"
            open(logfile,"x")

            #Set logging parameters
            logging.basicConfig(filename=logfile,encoding = "utf-8", level = logging.DEBUG, style = '{', format="{asctime} - {levelname} - {message}",datefmt="%Y-%m-%d %H:%M",force = True)
            logging.info(f"Program started by {os.getenv("username")}")

            logging.info(f"Clearing old log files")
            logclear(log_dest)

            #if user somehow gets here without choosing a client or a separator, error out. We need them.
            if not client or not sep:
                raise Exception("Client/Separator choice failed")
            
            logging.info(f'Importing images for {client} from {self.source} with "{sep}" as the separator')
            #Create archive directory for client if it does not exist
            arch = self.source + f'/archive'
            os.makedirs(arch,exist_ok=True)
        
            #Define image extensions
            image_extensions = ("*.png", "*.jpg", "*.gif")
            image_files = []

            #This grabs full image path, so no need to join on source when accessing the file. Can get the filename itself by using os.path.basename(file)
            for ext in image_extensions:
                image_files.extend(glob.glob(os.path.join(self.source, ext)))
            
            #Send error if no image files found, return to start
            if len(image_files) == 0:
                self.err_display("No files found, returning to start")
                self.client = None
                self.sep = None
                self.source = None
                self.show_start_screen()
                sys.exit()
            else:
                logging.info(f"{len(image_files)} image files found")

            #Loop around the image files in the source folder
            for image in image_files:
                #Check image size, skip if too big EDIT - max size increased as per Joe's email
                if os.path.getsize(image) > 512000:
                    messagebox.showinfo("Image too large",f"Image {os.path.basename(image)} too large. Skipping.")
                    logging.warning(f"Image {os.path.basename(image)} too large. Skipping.")
                    continue
                logging.info(f"Parsing file {os.path.basename(image)}")
                part = ''
                ino = 0
                #Get SKU and/or image number from the file name. If separator not in filename, assume you will want to get a new image number
                splitter = os.path.basename(image)
                img = splitter.split(".")[0]
                if sep in img:
                    part = img.split(sep)[0]
                    ino = img.split(sep)[1]
                else:
                    part = img
                    ino = self.getino(client,part)

                #Only want to import parts that exist, call method to check that.
                cont = self.check_part_exists(part,client)
                if cont == 0:
                    logging.info(f"Part {part} does not exist on database, skipped import")
                    continue

                if self.errorflag == 1:
                    self.err_display(f"Part check on {os.path.basename(image)} failed, check log for more details")
                    continue
                #If we somehow get here without a part or image number, skip file and contine
                if part == '' or ino == 0 or not ino:
                    logging.warning(f"Part number detection failed for file {os.path.basename(image)}")
                    self.err_display(f"Part number detection failed for file {os.path.basename(image)}")
                    continue
                
                #Dedupe checks (will insert/update as requested if a duplicate is found)
                logging.info(f"Checking for duplicates on part {part}, item no {ino} on client {client}")
                upd = self.dedupe(client,image,part,ino)

                if self.errorflag == 1:
                    self.err_display(f"File import failed on file {os.path.basename(image)}, check log for more details")
                    continue           
                
                #If no duplicates, insert the image
                if upd == 0:
                    logging.info(f"No duplicates found, inserting")
                    self.insertimage(client,image,part,ino)

                if self.errorflag == 1:
                    self.err_display(f"File import failed on file {os.path.basename(image)}, check log for more details")
                    continue
                
                #Archive the file
                logging.info("Archiving file")
                self.archivefile(image,arch)

            #End of file-loop, imports done, return to start screen
            logging.info("All files checked, process complete")
            messagebox.showinfo("GImage Import Finished","All files checked, process complete")
            self.source = None
            self.client = None
            self.sep = None
            self.show_start_screen()
        #Any exceptions, show the error and close the program
        except Exception as e:
            logging.error(f"{e}",exc_info = True)
            self.err_display(e)
            self.master.destroy()

    #Method to display errors (custom) - allows error displays without breaking algorithmic flow
    def err_display(self,e):
        def on_ok():
            error_window.destroy()

        error_window = tk.Toplevel()
        error_window.title("GImage Error")
        error_window.geometry("300x150")
        error_window.resizable(False, False)

        message = tk.Label(error_window, text=str(e), wraplength=280, justify="left", fg="red")
        message.pack(padx=10, pady=20)

        ok_button = tk.Button(error_window, text="OK", command=on_ok)
        ok_button.pack(pady=10)

        error_window.wait_window()

    #Method for the maintenance/display screens
    def launch_maintenance(self,maint=0):
        #Connection string to be used throughout the rest of the method
        conn_str = (
            "Driver={SQL Server};"
            "Server=SQL-SSRS;"
            "Database=Appz;"
            "Trusted_Connection=yes;"
        )
        conn = pyodbc.connect(conn_str)
        #Make the window title relevant
        window = tk.Toplevel()
        if maint == 1:
            window.title("GImage Maintenance")
        else:
            window.title("GImage Display")

        # Initialise Main Frames (detail frame comes in later)
        dropdown_frame = ttk.Frame(window)
        dropdown_frame.pack(pady=10)

        bcode_frame = ttk.Frame(window)
        bcode_frame.pack(pady = 10)

        part_frame = ttk.Frame(window)
        part_frame.pack(pady=10)

        image_frame = ttk.Frame(window)
        image_frame.pack(pady=10)

        # Tkinter variables
        clid_var = tk.StringVar()
        bcode_var = tk.StringVar()
        part_var = tk.StringVar()

        #Function to get client list
        def fetch_clids():
            cursor = conn.cursor()
            cursor.execute("SELECT clid, descr FROM dbo.clid WHERE descr IS NOT NULL ORDER BY descr")
            return cursor.fetchall()

        #Function to get part list (for client, that has image data)
        def fetch_parts(clid):
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT part FROM dbo.GImage_Data_v2 WHERE client = ?", clid)
            return [row.part for row in cursor.fetchall()]

        #Function to get image data
        def fetch_images(clid, part):
            cursor = conn.cursor()
            cursor.execute("SELECT ino, image_data FROM dbo.GImage_Data_v2 WHERE client = ? AND part = ? ORDER BY ino", clid, part)
            return cursor.fetchall()

        #Function to delete image (maintenance only)
        def delete_image(clid, part, ino):
            confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete image {ino}?")
            if confirm:
                try:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM dbo.GImage_Data_v2 WHERE client = ? AND part = ? AND ino = ?", clid, part, ino)
                    conn.commit()
                    messagebox.showinfo("Deleted", f"Image {ino} deleted successfully.")
                    show_images()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete image {ino}: {e}")

        
        #Function to create the rest of the input boxes once the client has been selected
        def on_clid_select(event=None):
            #Function to determine behaiviour of part drop-down menu
            def on_keypress(event):
                letter = event.char.lower()
                if event.keysym == "Tab" and part_combo.current() != -1:
                    show_images()
                    return
                elif not letter.isalnum():
                    return "break"
                current_index = part_combo.current()
                total_items = len(parts)
                for i in range(1, total_items + 1):
                    next_index = (current_index + i) % total_items
                    if parts[next_index].lower().startswith(letter):
                        part_combo.current(next_index)
                        break
                
                    
                return "break"
            #Get the client, clid and parts, destroy all the widgets in the part and barcode frames
            selected_text = clid_var.get()
            if not selected_text:
                return
            selected_clid = clid_map.get(selected_text)
            parts = fetch_parts(selected_clid)
            bcode_var.set('')
            part_var.set('')
            for widget in part_frame.winfo_children():
                widget.destroy()
            for widget in bcode_frame.winfo_children():
                widget.destroy()
            if parts:
                #Recreate widgets in part and barcode frames if the client has any parts in the GImage tables.
                ttk.Label(bcode_frame,text = "Barcode:").pack(side = tk.LEFT)
                bcode_entry = ttk.Entry(bcode_frame,textvariable=bcode_var)
                bcode_entry.pack(side=tk.LEFT)
                ttk.Label(part_frame, text="Select/Search Part:").pack(side=tk.LEFT)
                search_entry = ttk.Entry(part_frame, textvariable=part_var)
                search_entry.pack(side=tk.LEFT)
                part_combo = ttk.Combobox(part_frame, values=parts, textvariable=part_var)
                part_combo.pack(side=tk.LEFT)
                part_combo.bind("<<ComboboxSelected>>", lambda e: show_images())
                part_combo.bind("<Key>", on_keypress)
                search_entry.bind("<Return>", lambda e: show_images())
                search_entry.bind("<Tab>", lambda e: show_images())
                bcode_entry.bind("<Return>", lambda e: show_images())
                bcode_entry.bind("<Tab>", lambda e: show_images())

        #Function to get the part from the barcode
        def part_get(clid,bcode):
            conn_str = (
            "Driver={SQL Server};"
            "Server=SQL-SSRS;"
            "Database=Appz;"
            "Trusted_Connection=yes;"
            )
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("EXEC GImage_Bcode_Search ?, ?", bcode, clid)
            row = cursor.fetchone()
            conn.commit()
            return row[0] if row else None
        
        #Function to get the part details (default bin, weights etc)
        def detail_get(clid,part):
            conn_str = (
            "Driver={SQL Server};"
            "Server=SQL-SSRS;"
            "Database=Appz;"
            "Trusted_Connection=yes;"
            )
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("EXEC GImage_Part_Details ?, ?",part,clid)
            row = cursor.fetchone()
            conn.commit()
            return row if row else None

        #Function to show images
        def show_images():
            #Destroy widgets in the image frame
            for widget in image_frame.winfo_children():
                widget.destroy()

            #Get client, part and barcode details
            selected_text = clid_var.get()
            selected_bcode = bcode_var.get()
            selected_part = part_var.get()
            #if we don't have a client, or we don't have either a part or barcode, stop
            if not selected_text or not (selected_part or selected_bcode):
                return
            #Get clid from client
            selected_clid = clid_map.get(selected_text)

            #If we have a barcode but no part, get the part from the barcode
            if not selected_part and selected_bcode:
                selected_part = part_get(selected_clid,selected_bcode)
            
            #Grab them images
            images = fetch_images(selected_clid, selected_part)

            #If there are no images for whatever reason, let the user know
            if not images:
                ttk.Label(image_frame, text="No images found.",font=self.font).pack()
                return

            #Start at image index 0
            current_index = tk.IntVar(value=0)

            #Function to update the display
            def update_display():
                #Destroy widgets in the image frame
                for widget in image_frame.winfo_children():
                    widget.destroy()
                #Get item number and image date from the current image index
                ino, img_data = images[current_index.get()]
                try:
                    #Get details, if we have any, display the current SKU and description
                    details = detail_get(selected_clid,selected_part)
                    if details:
                        descr = details[0]
                        descr_frame = tk.Frame(image_frame)
                        descr_frame.pack()
                        descr_label = tk.Label(descr_frame,text = f"{selected_part}: {descr}",font = self.font)
                        descr_label.pack(pady=5)
                    
                    #Get image data, resize it to 300x300, make it lookable at
                    img = Image.open(io.BytesIO(img_data))
                    img = img.resize((300, 300))
                    photo = ImageTk.PhotoImage(img)
                    
                    #Show image in image frame
                    img_label = tk.Label(image_frame, image=photo)
                    img_label.image = photo
                    img_label.pack(pady=5)

                    #Show which image it is
                    count_label = tk.Label(image_frame, text=f"Image {current_index.get() + 1} of {len(images)}",font = self.font)
                    count_label.pack(pady=5)

                    #Button frame (left and right button functions are further down)
                    btn_frame = tk.Frame(image_frame)
                    btn_frame.pack()

                    # ← button
                    prev_btn = ttk.Button(btn_frame, text="←", command=show_prev)
                    prev_btn.grid(row=0, column=0, padx=5)

                    # Delete button (Only shown in Maintenance screen)
                    if maint == 1:
                        del_btn = ttk.Button(btn_frame, text=f"Delete Image {ino}",
                                             command=lambda: delete_image(selected_clid, selected_part, ino))
                        del_btn.grid(row=0, column=1, padx=5)

                    # → button
                    next_btn = ttk.Button(btn_frame, text="→", command=show_next)
                    next_btn.grid(row=0, column=2, padx=5)

                    #If we have details, grab and put them below the buttons (order of details decided by SQL table, so will not change(tm)) 3 Frames packed down here - Notes frame, detail frame and supl frame
                    if details:
                        notes = details[1]
                        def_bin = details[2]
                        def_store = details[3]
                        def_supl = details[4]
                        stock = details[5]
                        allocated = details[6]
                        weight = details[7]
                        volume = details[8]
                        supl_part = details[9]
                        notes_frame = tk.Frame(image_frame)
                        notes_frame.pack()
                        note_label = tk.Label(notes_frame,text = f"Goods In Notes:\n {notes}",font =self.font)
                        note_label.pack(pady=5)
                        detail_frame = tk.Frame(image_frame)
                        detail_frame.pack()
                        def_bin_txt = tk.Label(detail_frame,text = f"Default Bin:",font=self.font)
                        def_bin_txt.grid(row=0,column=0,padx = 5, pady = 5)
                        def_bin_label = tk.Label(detail_frame,text = def_bin,font = self.font)
                        def_bin_label.grid(row = 0, column = 1, padx = 5, pady = 5)
                        def_store_txt = tk.Label(detail_frame,text = f"Default Store:",font = self.font)
                        def_store_txt.grid(row = 1,column=0,padx = 5, pady = 5)
                        def_store_label = tk.Label(detail_frame,text = def_store,font = self.font)
                        def_store_label.grid(row = 1, column = 1, padx = 5, pady = 5)
                        stock_txt = tk.Label(detail_frame,text = f"Stock:",font = self.font)
                        stock_txt.grid(row = 0,column = 2,pady = 5, padx=5)
                        stock_label = tk.Label(detail_frame,text = stock,font = self.font)
                        stock_label.grid(row = 0, column = 3, pady = 5, padx=5)
                        aloc_txt = tk.Label(detail_frame,text = f"Allocated:",font = self.font)
                        aloc_txt.grid(row = 1,column = 2, pady = 5, padx = 5)
                        aloc_label = tk.Label(detail_frame, text = allocated, font = self.font)
                        aloc_label.grid(row = 1, column = 3, pady = 5, padx = 5)
                        weight_txt = tk.Label(detail_frame,text = "Weight:", font = self.font)
                        weight_txt.grid(row = 2, column = 0, pady = 5, padx = 5)
                        weight_label = tk.Label(detail_frame,text = weight,font = self.font)
                        weight_label.grid(row = 2, column = 1, pady = 5, padx = 5)
                        volume_txt = tk.Label(detail_frame, text = "Volume:", font=self.font)
                        volume_txt.grid(row = 2, column = 2, pady = 5, padx = 5)
                        volume_label = tk.Label(detail_frame, text = volume,font=self.font)
                        volume_label.grid(row = 2, column = 3, pady=5,padx=5)
                        supl_frame = tk.Frame(image_frame)
                        supl_frame.pack()
                        def_supl_label = tk.Label(supl_frame,text = f"Default Supplier: {def_supl}",font = self.font)
                        def_supl_label.grid(row = 0, column = 0, pady = 5)
                        supl_part_label = tk.Label(supl_frame,text = f"Supplier Part: {supl_part}", font = self.font)
                        supl_part_label.grid(row = 1, column = 0, pady = 5)

                except Exception as e:
                    #Show error if the image failed to load
                    ttk.Label(image_frame, text=f"Failed to load image {ino}: {e}").pack()
            
            #Functions for next and previous buttons
            def show_next():
                if current_index.get() < len(images) - 1:
                    current_index.set(current_index.get() + 1)
                    update_display()

            def show_prev():
                if current_index.get() > 0:
                    current_index.set(current_index.get() - 1)
                    update_display()
            #showing images updates the display
            update_display()
        
        #Define behaviour when user puts in letter while highlighting client dropdown
        def on_clidpress(event):
                letter = event.char.lower()
                if event.keysym == "Tab" and clid_dropdown.current() != -1:
                    on_clid_select()
                    return
                elif not letter.isalpha():
                    return "break"
                current_index = clid_dropdown.current()
                total_items = len(list(clid_map.keys()))
                for i in range(1, total_items + 1):
                    next_index = (current_index + i) % total_items
                    if list(clid_map.keys())[next_index].lower().startswith(letter):
                        clid_dropdown.current(next_index)
                        break
                return "break"
        # Load client list into dropdown box
        ttk.Label(dropdown_frame, text="Select Client:").pack(side=tk.LEFT)
        clids = fetch_clids()  # list of (clid, descr)
        clid_map = {descr: clid for clid, descr in clids}  # map descr -> clid
        clid_dropdown = ttk.Combobox(dropdown_frame, textvariable=clid_var,
                             values=list(clid_map.keys()))
        clid_dropdown.pack(side=tk.LEFT)
        clid_dropdown.bind("<<ComboboxSelected>>", on_clid_select)
        clid_dropdown.bind("<Key>", on_clidpress)
        #loop window
        window.wait_window()
        #Once done, clear globals and either go back to start screen or close the program depending on if this is the maintenance version of the app
        self.source = None
        self.client = None
        self.sep = None
        if self.maint == 1:
            self.show_start_screen()
        else:
            self.master.destroy()


#Function to clear the log files
def logclear(path, suffix = ".log"):
    for f in os.listdir(path):
        g = os.path.join(path, f)
        if g.endswith(suffix):
            if os.stat(g).st_mtime < time.time() - (30 * 86400):
                if os.path.isfile(g):
                    os.remove(g)

#function to convert an image from the file to binary that can be read/put in database
def convert_image_to_binary(image_path):
    with open(image_path, 'rb') as file:
        return file.read()

#Create main tk screen to layer everything else on top of, initiate the app
def main(maint = 1):
    root = tk.Tk()
    app = GImageApp(root,maint)
    root.mainloop()



#Only go into "maintenance" mode if there are no extra arguments (ie running it from the script) or the 1 extra argument is "maint"
if __name__ == "__main__":
    if len(sys.argv) == 2:
        maint = 0
        if sys.argv[1] == "maint":
            maint = 1
        main(maint)
    else:
        main()

