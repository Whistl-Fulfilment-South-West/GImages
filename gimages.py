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
from tkinter import filedialog



class GImageApp:
    def __init__(self, master,source,client,sep):
        self.master = master
        self.master.title("GImages")
        self.source = source
        self.client = client
        self.sep = sep
        self.errorflag = 0
        self.show_start_screen()
    
    def show_start_screen(self):
        self.master.withdraw()
        res = {'choice': None}

        def maint():
            res["choice"] = 'maint'
            start_window.destroy()

        def imp():
            res["choice"] = 'imp'
            start_window.destroy()

        def exit_app():
            self.master.destroy()
        
        def on_close():
            self.master.destroy()

        start_window = tk.Toplevel()
        start_window.title("GImages")
        start_window.geometry("300x180")  

        start_window.protocol("WM_DELETE_WINDOW", on_close)
        
        message = tk.Label(start_window, text="Choose your action", wraplength=280, justify="left")
        message.pack(padx=10, pady=20)

        button_frame = tk.Frame(start_window)
        button_frame.pack(pady=10)

        button_width = 15

        maint_button = tk.Button(button_frame, text="Maintenance", command=maint, width=button_width)
        maint_button.grid(row=0, column=0, padx=10)

        imp_button = tk.Button(button_frame, text="Import", command=imp, width=button_width)
        imp_button.grid(row=0, column=1, padx=10)
        
        exit_button = tk.Button(start_window, text="Exit", command=exit_app, width=button_width)
        exit_button.pack(pady=5)

        start_window.wait_window()
        if res["choice"] == 'maint':
            self.launch_maintenance()
        elif res["choice"] == 'imp':
            self.launch_import()


    def show_error(self,e):
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

            def on_ok():
                selected_descr = combo.get()
                selected_value["value"] = descr_to_clid.get(selected_descr)
                main_window.destroy()

            def on_selection(event):
                ok_button.config(state="normal")

            def on_keypress(event):
                letter = event.char.lower()
                if not letter.isalpha():
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

            combo = ttk.Combobox(main_window, state="readonly", values=descr_list)
            combo.place(x=50, y=40)
            combo.bind("<<ComboboxSelected>>", on_selection)
            combo.bind("<Key>", on_keypress)

            ok_button = tk.Button(main_window, text="OK", state="disabled", command=on_ok)
            ok_button.place(x=130, y=90)

            main_window.wait_window()

            return selected_value["value"]
        
        except Exception as e:
            logging.error(f"Error: {e}", exc_info=True)
        return
    def sepchoose(self):
        separator_value = {"value": None}

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

        label = tk.Label(root, text="Enter a single character separator:")
        label.pack(pady=10)

        hint_label = tk.Label(root, text="If no separator used in your files,\n"
                                        "please enter a single digit not in your filenames.",
                            wraplength=280, justify="center", fg="gray")
        hint_label.pack(pady=(0, 10))

        entry = tk.Entry(root, width=5, justify="center")
        entry.pack()
        entry.bind("<KeyRelease>", on_key_release)

        ok_button = tk.Button(root, text="OK", command=on_ok, state="disabled")
        ok_button.pack(pady=10)

        root.wait_window()
        return separator_value["value"]
        
    def getino(self,client,part):
        server = 'SQL-SSRS'
        database = 'Appz'
        try:
            cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';Trusted_Connection=yes')
            cursor = cnxn.cursor()
            query = "EXEC GImage_getino ?,?"
            cursor.execute(query,(client,part))
            nuino = cursor.fetchone()
            return int(nuino[0]) + 1

        except Exception as e:
            logging.error(f"Error: {e}", exc_info = True)
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'cnxn' in locals():
                cnxn.close()

    def check_part_exists(self,part,client):
        server = 'SQL-SSRS'
        database = 'Appz'
        try:
            # Connect to DB and fetch client data
            cnxn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes')
            cursor = cnxn.cursor()
            cursor.execute("EXEC GImage_PartCheck ?, ?", part, client)
            row = cursor.fetchone()

            if row:
                return 1
            else:
                # Part does not exist – show message box
                root = tk.Tk()
                root.withdraw()
                messagebox.showinfo("Part Not Found", f"Part {part} does not exist on {client}. Skipping.")
                root.destroy()
                return 0

        except Exception as e:
            logging.error(f"Error: {e}", exc_info=True)
            self.errorflag = 1
            return

        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'cnxn' in locals():
                cnxn.close()


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
            if 'cursor' in locals():
                cursor.close()
            if 'cnxn' in locals():
                cnxn.close()   

    def choose_image_version(self,old_image_bytes, new_image_bytes, client, image, part, ino):
        result = {"choice": None}

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
        old_label = tk.Label(image_frame, text="Old Image\n", compound="top")
        old_label.image = old_photo  # Keep reference
        old_label.configure(image=old_photo)
        old_label.pack(side="left", padx=10)
        
        #enter new image
        new_label = tk.Label(image_frame, text="New Image\n", compound="top")
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

        #add old image as new image
        add_new_btn = tk.Button(btn_frame, text="Add As New Image", command=add_new, width=42)
        add_new_btn.grid(row=1, column=0, columnspan=2, pady=(10, 0))

        # Let Tkinter auto-size the window
        window.wait_window()


        if result["choice"] == "Y":
            return 1
        elif result["choice"] == "N":
            return 0
        else:
            logging.info("No selection made. Discarding new image.")
            return 0
        

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
            if 'cursor' in locals():
                cursor.close()
            if 'cnxn' in locals():
                cnxn.close()  
    
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
            cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';Trusted_Connection=yes')
            cursor = cnxn.cursor()
            query = """EXEC GImage_dedupe ?, ?, ?"""
            cursor.execute(query, (part, client, ino))
            exists = cursor.fetchone()[0] > 0

            if exists:
                logging.warning("Part %s, image no %s already exists for %s", part, ino, client)
                grabmage = """EXEC GImage_grabimage ?, ?, ?"""
                cursor.execute(grabmage, (part, client, ino))
                olimage = cursor.fetchone()[0]
                nuimage = convert_image_to_binary(image)
                logging.info("Requesting decision from user")
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
            if 'cursor' in locals():
                cursor.close()
            if 'cnxn' in locals():
                cnxn.close()    
    



    def launch_import(self):
        try:
            self.master.withdraw()
            client = self.client
            sep = self.sep

                                     
            if not client:
                client = self.clientchoose()
            if not sep:
                sep = self.sepchoose()

            if not client:
                self.err_display("Import failed - Please choose client and separator")
                self.show_start_screen()

            if not self.source:
                self.source = '//Elucid9/Elucid/Data_Import/Gimage/' + client
                os.makedirs(self.source,exist_ok=True)
                messagebox.showinfo("GImages Source",f"Images will be downloaded from {self.source}")

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

            if not client or not sep:
                raise Exception("Client/Separator choice failed")
            
            logging.info(f'Importing images for {client} from {self.source} with "{sep}" as the separator')
            #Create archive directory for client if it does not exist
            arch = self.source + f'/archive'
            os.makedirs(arch,exist_ok=True)
        
            #Define image extensions
            image_extensions = ("*.png", "*.jpg", "*.gif")
            image_files = []

            for ext in image_extensions:
                image_files.extend(glob.glob(os.path.join(self.source, ext)))
            #This grabs full image path, so no need to join on source when accessing the file. Can get the filename itself by using os.path.basename(file)
            
            if len(image_files) == 0:
                raise Exception("No files found - exiting")
            else:
                logging.info(f"{len(image_files)} image files found")

            for image in image_files:
                #Check image size, skip if too big
                if os.path.getsize(image) > 256000:
                    messagebox.showinfo("Image too large",f"Image {os.path.basename(image)} too large. Skipping.")
                    logging.warning(f"Image {os.path.basename(image)} too large. Skipping.")
                    continue
                logging.info(f"Parsing file {os.path.basename(image)}")
                part = ''
                ino = 0
                splitter = os.path.basename(image)
                img = splitter.split(".")[0]
                if sep in img:
                    part = img.split(sep)[0]
                    ino = img.split(sep)[1]
                else:
                    part = img
                    ino = self.getino(client,part)

                cont = self.check_part_exists(part,client)
                if cont == 0:
                    logging.info(f"Part {part} does not exist on database, skipped import")
                    continue

                if self.errorflag == 1:
                    self.err_display(f"Part check on {os.path.basename(image)} failed, check log for more details")
                    continue

                if part == '' or ino == 0 or not ino:
                    logging.warning(f"Part number detection failed for file {os.path.basename(image)}")
                    self.err_display(f"Part number detection failed for file {os.path.basename(image)}")
                    continue
                logging.info(f"Checking for duplicates on part {part}, item no {ino} on client {client}")
                upd = self.dedupe(client,image,part,ino)

                if self.errorflag == 1:
                    self.err_display(f"File import failed on file {os.path.basename(image)}, check log for more details")
                    continue           
                
                if upd == 0:
                    logging.info(f"No duplicates found, inserting")
                    self.insertimage(client,image,part,ino)

                if self.errorflag == 1:
                    self.err_display(f"File import failed on file {os.path.basename(image)}, check log for more details")
                    continue

                logging.info("Archiving file")
                self.archivefile(image,arch)
        
            logging.info("All files checked, process complete")
            messagebox.showinfo("GImage Import Finished","All files checked, process complete")
            self.show_start_screen()
        except Exception as e:
           
            logging.error(f"{e}",exc_info = True)
            self.err_display(e)
            self.master.destroy()

        
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

    def launch_maintenance(self):
        conn_str = (
            "Driver={ODBC Driver 17 for SQL Server};"
            "Server=SQL-SSRS;"
            "Database=Appz;"
            "Trusted_Connection=yes;"
        )
        conn = pyodbc.connect(conn_str)

        window = tk.Toplevel()
        window.title("GImage Maintenance")

        # Frames
        dropdown_frame = ttk.Frame(window)
        dropdown_frame.pack(pady=10)

        part_frame = ttk.Frame(window)
        part_frame.pack(pady=10)

        image_frame = ttk.Frame(window)
        image_frame.pack(pady=10)

        # Tkinter variables
        clid_var = tk.StringVar()
        part_var = tk.StringVar()

        def fetch_clids():
            cursor = conn.cursor()
            cursor.execute("SELECT clid, descr FROM dbo.clid WHERE descr IS NOT NULL ORDER BY descr")
            return cursor.fetchall()

        def fetch_parts(clid):
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT part FROM dbo.GImage_Data_v2 WHERE client = ?", clid)
            return [row.part for row in cursor.fetchall()]

        def fetch_images(clid, part):
            cursor = conn.cursor()
            cursor.execute("SELECT ino, image_data FROM dbo.GImage_Data_v2 WHERE client = ? AND part = ? ORDER BY ino", clid, part)
            return cursor.fetchall()

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

        def on_clid_select(event=None):
            selected_text = clid_var.get()
            if not selected_text:
                return
            selected_clid = clid_map.get(selected_text)
            parts = fetch_parts(selected_clid)
            part_var.set('')
            for widget in part_frame.winfo_children():
                widget.destroy()
            if parts:
                ttk.Label(part_frame, text="Select/Search Part:").pack(side=tk.LEFT)
                search_entry = ttk.Entry(part_frame, textvariable=part_var)
                search_entry.pack(side=tk.LEFT)
                part_combo = ttk.Combobox(part_frame, values=parts, textvariable=part_var)
                part_combo.pack(side=tk.LEFT)
                part_combo.bind("<<ComboboxSelected>>", lambda e: show_images())
                search_entry.bind("<Return>", lambda e: show_images())

        def show_images():
            for widget in image_frame.winfo_children():
                widget.destroy()

            selected_text = clid_var.get()
            selected_part = part_var.get()
            if not selected_text or not selected_part:
                return

            selected_clid = clid_map.get(selected_text)
            images = fetch_images(selected_clid, selected_part)
            if not images:
                ttk.Label(image_frame, text="No images found.").pack()
                return

            current_index = tk.IntVar(value=0)

            def update_display():
                for widget in image_frame.winfo_children():
                    widget.destroy()
                ino, img_data = images[current_index.get()]
                try:
                    img = Image.open(io.BytesIO(img_data))
                    img = img.resize((200, 200))
                    photo = ImageTk.PhotoImage(img)

                    img_label = tk.Label(image_frame, image=photo)
                    img_label.image = photo
                    img_label.pack(pady=5)

                    count_label = tk.Label(image_frame, text=f"Image {current_index.get() + 1} of {len(images)}")
                    count_label.pack(pady=5)

                    btn_frame = tk.Frame(image_frame)
                    btn_frame.pack()

                    # ← button
                    prev_btn = ttk.Button(btn_frame, text="←", command=show_prev)
                    prev_btn.grid(row=0, column=0, padx=5)

                    # Delete button
                    del_btn = ttk.Button(btn_frame, text=f"Delete Image {ino}",
                                         command=lambda: delete_image(selected_clid, selected_part, ino))
                    del_btn.grid(row=0, column=1, padx=5)

                    # → button
                    next_btn = ttk.Button(btn_frame, text="→", command=show_next)
                    next_btn.grid(row=0, column=2, padx=5)

                except Exception as e:
                    ttk.Label(image_frame, text=f"Failed to load image {ino}: {e}").pack()

            def show_next():
                if current_index.get() < len(images) - 1:
                    current_index.set(current_index.get() + 1)
                    update_display()

            def show_prev():
                if current_index.get() > 0:
                    current_index.set(current_index.get() - 1)
                    update_display()

            update_display()

        # Load client list
        ttk.Label(dropdown_frame, text="Select Client:").pack(side=tk.LEFT)
        clids = fetch_clids()  # list of (clid, descr)
        clid_map = {descr: clid for clid, descr in clids}  # map descr -> clid
        clid_dropdown = ttk.Combobox(dropdown_frame, textvariable=clid_var,
                             values=list(clid_map.keys()))
        clid_dropdown.pack(side=tk.LEFT)
        clid_dropdown.bind("<<ComboboxSelected>>", on_clid_select)
        window.wait_window()

        self.show_start_screen()

def logclear(path, suffix = ".log"):
    for f in os.listdir(path):
        g = os.path.join(path, f)
        if g.endswith(suffix):
            if os.stat(g).st_mtime < time.time() - (30 * 86400):
                if os.path.isfile(g):
                    os.remove(g)

def convert_image_to_binary(image_path):
    with open(image_path, 'rb') as file:
        return file.read()

def main(source = None,client = None,sep = None):
    root = tk.Tk()
    app = GImageApp(root,source,client,sep)
    root.mainloop()



#Running main - if we have all 3 arguments, pass them to the main function. If we have 2 arguments, should be the source and the client. If we have 1 argument, should be the source. If we have 0 arguments, run the function with default settings. Otherwise, leave message as to why fail, then exit.
if __name__ == "__main__":
    if len(sys.argv) == 4:
        source = sys.argv[1]
        client = sys.argv[2]
        sep = sys.argv[3]
        main(source,client,sep)

    elif len(sys.argv) == 3:
        source = sys.argv[1]
        client = sys.argv[2]
        main(source,client)

    elif len(sys.argv) == 2:
        source = sys.argv[1]
        main(source)

    else:
        main()

