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

def convert_image_to_binary(image_path):
    with open(image_path, 'rb') as file:
        return file.read()

    
def getino(client,part):
    global errorflag
    server = 'SQL-SSRS'
    database = 'Appz'
    try:
        cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';Trusted_Connection=yes')
        cursor = cnxn.cursor()
        query = "SELECT ISNULL(MAX(ino),0) FROM GImage_Data_v2 WHERE client = ? and part = ?"
        cursor.execute(query,(client,part))
        nuino = cursor.fetchone()
        return int(nuino) + 1

    except Exception as e:
        logging.error(f"Error: {e}", exc_info = True)
        errorflag = 1
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'cnxn' in locals():
            cnxn.close()   


def insertimage(client, image, part, ino):
    global errorflag
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
        errorflag = 1
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'cnxn' in locals():
            cnxn.close()   

def updateimage(client, image, part, ino):
    global errorflag
    server = 'SQL-SSRS'
    database = 'Appz'
    image_binary = convert_image_to_binary(image)
    try:
        cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';Trusted_Connection=yes')
        cursor = cnxn.cursor()
        query = """EXEC GImage_Update ?, ?, ?, ?"""
        cursor.execute(query,(client,image_binary,part,ino))
    except Exception as e:
        logging.error(f"Error: {e}", exc_info = True)
        errorflag = 1
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'cnxn' in locals():
            cnxn.close()   

def dedupe(client,image, part, ino):
    #returns 1 if duplicate found (and dedupe done one way or the other), 0 if not
    global errorflag
    server = 'SQL-SSRS'
    database = 'Appz'
    try:
        cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';Trusted_Connection=yes')
        cursor = cnxn.cursor()
        query = """SELECT COUNT(*) FROM GImage_Data_v2 WHERE part = ? AND client = ? AND ino = ?"""
        cursor.execute(query, (part, client, ino))
        exists = cursor.fetchone()[0] > 0

        if exists:
            logging.warning("Part %s, image no %s already exists for %s", part, ino, client)
            grabmage = """SELECT image FROM GImage_Data_v2 WHERE part = ? AND client = ? AND ino = ?"""
            cursor.execute(grabmage, (part, client, ino))
            olimage = cursor.fetchone()
            nuimage = convert_image_to_binary(image)
            logging.info("Requesting decision from user")
            ans = choose_image_version(olimage,nuimage,client,image,part,ino)
            if ans == 1:
                updateimage(client,image,part,ino)
            return 1
            # displayimages(nuimage,olimage)
            # retry = 0
            # while retry  <  10:
            #     inp = input("Do you want to overwrite the old image (Y/N)?").strip().upper()
            #     if inp == "Y":
            #         logging.info("Overwriting old image")
            #         updateimage(client,image,part,ino)
            #         return 1
            #     elif inp == "N":
            #         logging.info("Discarding new image")
            #         print("Skipping file")
            #         return 1
            #     else:
            #         print("Invalid option, please enter Y or N")
            #         retry =+ 1
            # print("Too many retries, discarding new image")
            # return 1
            
        else:
            return 0
        
    except Exception as e:
        logging.error(f"Error: {e}", exc_info = True)
        errorflag = 1

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'cnxn' in locals():
            cnxn.close()    
        

def choose_image_version(old_image_bytes, new_image_bytes, client, image, part, ino):
    result = {"choice": None}

    def use_new():
        logging.info("Overwriting old image")
        updateimage(client, image, part, ino)
        result["choice"] = "Y"
        window.destroy()

    def keep_old():
        logging.info("Discarding new image")
        print("Skipping file")
        result["choice"] = "N"
        window.destroy()

    # Convert binary to PhotoImage via PIL
    old_img = Image.open(io.BytesIO(old_image_bytes))
    new_img = Image.open(io.BytesIO(new_image_bytes))

    # Resize to fit window if needed
    max_size = (300, 300)
    old_img.thumbnail(max_size)
    new_img.thumbnail(max_size)

    old_photo = ImageTk.PhotoImage(old_img)
    new_photo = ImageTk.PhotoImage(new_img)

    # Setup tkinter window
    window = tk.Tk()
    window.title(f"Compare Images - {part}")
    window.geometry("650x400")

    tk.Label(window, text="Old Image").pack(side="left", padx=20, pady=10)
    tk.Label(window, text="New Image").pack(side="right", padx=20, pady=10)

    old_label = tk.Label(window, image=old_photo)
    old_label.image = old_photo  # Keep reference
    old_label.pack(side="left", padx=20)

    new_label = tk.Label(window, image=new_photo)
    new_label.image = new_photo
    new_label.pack(side="right", padx=20)

    # Buttons
    btn_frame = tk.Frame(window)
    btn_frame.pack(pady=10)

    keep_old_btn = tk.Button(btn_frame, text="Keep Old Image", command=keep_old, width=20)
    keep_old_btn.grid(row=0, column=0, padx=10)

    use_new_btn = tk.Button(btn_frame, text="Use New Image", command=use_new, width=20)
    use_new_btn.grid(row=0, column=1, padx=10)

    window.mainloop()

    if result["choice"] == "Y":
        return 1
    elif result["choice"] == "N":
        return 0
    else:
        logging.info("No selection made. Discarding new image.")
        return 0
    
    

def displayimages(im1,im2):
    image1 = Image.open(io.BytesIO(im1))
    image2 = Image.open(io.BytesIO(im2))
    
    # Resize images to the same height (optional)
    height = min(image1.height, image2.height)
    image1 = image1.resize((int(image1.width * (height / image1.height)), height))
    image2 = image2.resize((int(image2.width * (height / image2.height)), height))
    
    # Create new image with enough width to hold both
    new_width = image1.width + image2.width
    new_image = Image.new('RGB', (new_width, height))
    
    # Paste images side by side
    new_image.paste(image1, (0, 0))
    new_image.paste(image2, (image1.width, 0))
    
    # Show the result
    new_image.show()


def archivefile(image,dest):
    suffix = os.path.splitext(image)[1]
    file = os.path.basename(image)
    ind = file.find(suffix)
    nufile = file[:ind] + datetime.now().strftime("%Y%m%dT%H%M%S") + file[ind:]
    os.rename(image, dest + "/" + nufile)

def logclear(path, suffix = ".log"):
    for f in os.listdir(path):
        g = os.path.join(path, f)
        if g.endswith(suffix):
            if os.stat(g).st_mtime < time.time() - (30 * 86400):
                if os.path.isfile(g):
                    os.remove(g)


def clientchoose():
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

        main_window = tk.Tk()
        main_window.title("Choose Client")
        main_window.geometry("350x150")

        combo = ttk.Combobox(main_window, state="readonly", values=descr_list)
        combo.place(x=50, y=40)
        combo.bind("<<ComboboxSelected>>", on_selection)
        combo.bind("<Key>", on_keypress)

        ok_button = tk.Button(main_window, text="OK", state="disabled", command=on_ok)
        ok_button.place(x=130, y=90)

        main_window.mainloop()

        return selected_value["value"]

    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        return

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'cnxn' in locals():
            cnxn.close()
    
def check_part_exists(part,client):
    server = 'SQL-SSRS'
    database = 'Appz'
    global errorflag
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
        errorflag = 1
        return

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'cnxn' in locals():
            cnxn.close()

def sepchoose():
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

    root = tk.Tk()
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

    root.mainloop()
    return separator_value["value"]

#function to display error
def err_display(e):
    def on_ok():
        error_window.destroy()

    error_window = tk.Tk()
    error_window.title("GImage Error")
    error_window.geometry("300x150")
    error_window.resizable(False, False)

    message = tk.Label(error_window, text=str(e), wraplength=280, justify="left", fg="red")
    message.pack(padx=10, pady=20)

    ok_button = tk.Button(error_window, text="OK", command=on_ok)
    ok_button.pack(pady=10)

    error_window.mainloop()

    
def main(source = 'C:/Development/python/gimages',client = None,sep = None):

    #client = 'TEST', sep = '_'
    #Make sure main function accesses the global "errorflag" variable (not necessary at time of writing)
    global errorflag

    #Make sure log folder exists, make it if not
    log_dest = source + f"/logs"
    os.makedirs(log_dest,exist_ok=True)

    #Setup logging - create log file
    logfile = f"{log_dest}/log{datetime.now().strftime("%Y%m%dT%H%M%S")}.log"
    open(logfile,"x")

    #Set logging parameters
    logging.basicConfig(filename=logfile,encoding = "utf-8", level = logging.DEBUG, style = '{', format="{asctime} - {levelname} - {message}",datefmt="%Y-%m-%d %H:%M",force = True)
    logging.info(f"Program started by {os.getenv("username")}")

    logging.info(f"Clearing old log files")
    logclear(log_dest)
    try:
        #if client not set, let user choose
        if not client:
            logging.info("Querying client")
            client = clientchoose()

        #if seperator not set, let user choose
        if not sep:
            logging.info("Querying seperator")
            sep = sepchoose()

        #if separator or client still not set, quit - something went wrong
        if not client or not sep:
            raise Exception("Client/Separator choice failed")
        
        logging.info(f'Importing images for {client} from {source} with "{sep}" as the separator')

        #Create archive directory for client if it does not exist
        arch = source + f'/{client}/archive'
        os.makedirs(arch,exist_ok=True)
        
        image_extensions = ("*.png", "*.jpg", "*.gif")
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(source, ext)))
        #This grabs full image path, so no need to join on source when accessing the file. Can get the filename itself by using os.path.basename(file)
            
        if len(image_files) == 0:
            raise Exception("No files found")
        else:
            logging.info(f"{len(image_files)} image files found")
        
        for image in image_files:
            if os.path.getsize(image) > 256000:
                print(f"Image {os.path.basename(image)} too large. Skipping.")
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
                ino = getino(client,part)

            cont = check_part_exists(part,client)
            if cont == 0:
                logging.info(f"Part {part} does not exist on database, skipped import")
                continue

            if errorflag == 1:
                err_display(f"Part check on {os.path.basename(image)} failed, check log for more details")
                continue

            if part == '' or ino == 0 or not ino:
                logging.warning(f"Part number detection failed for file {os.path.basename(image)}")
                err_display(f"Part number detection failed for file {os.path.basename(image)}")
                continue
            logging.info(f"Checking for duplicates on part {part}, item no {ino} on client {client}")
            upd = dedupe(client,image,part,ino)

            if errorflag == 1:
                err_display(f"File import failed on file {os.path.basename(image)}, check log for more details")
                continue           
            
            if upd == 0:
                logging.info(f"No duplicates found, inserting")
                insertimage(client,image,part,ino)

            if errorflag == 1:
                err_display(f"File import failed on file {os.path.basename(image)}, check log for more details")
                continue

            logging.info("Archiving file")
            archivefile(image,arch)
        
        logging.info("All files checked, process complete")
        

    except Exception as e:
        logging.error(f"{e}",exc_info = True)
        err_display(e)

#Initialising error flag to exit loops when SQL fails
errorflag = 0

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

    elif len(sys.argv) > 4:
        err_display("Incorrect number of arguments, please contact a member of the IS team")

    else:
        main()