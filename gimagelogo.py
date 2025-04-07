import sys
import time
import os
from datetime import datetime
import logging
import glob

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
        #get values from database - CHANGE SQL QUERY WHEN WE DECIDE WHERE THIS IS COMING FROM
        cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';Trusted_Connection=yes')
        cursor = cnxn.cursor()
        query = "SELECT Description FROM Onestock_Clients"
        cursor.execute(query)
        clients = [row.Description for row in cursor]

        selected_value = {"value": None} 
        
        #subfunction for getting value
        def on_ok():
            selected_value["value"] = combo.get()
            main_window.destroy()
        
        #subfunction for first selection of something
        def on_selection(event):
            ok_button.config(state="normal")

        #subfunction for keypress
        def on_keypress(event):
            letter = event.char.lower()
            if not letter.isalpha():
                return

            current_index = combo.current()
            total_items = len(clients)

            # Find next item starting with the pressed letter
            for i in range(1, total_items + 1):
                next_index = (current_index + i) % total_items
                if clients[next_index].lower().startswith(letter):
                    combo.current(next_index)
                    break

        # create basic GUI
        main_window = tk.Tk()
        main_window.config(width=300, height=200)
        main_window.title("Choose Client")

        #create dropdown menu
        combo = ttk.Combobox(main_window, state="readonly", values=clients)
        combo.place(x=50, y=50)
        combo.bind("<<ComboboxSelected>>", on_selection)
        combo.bind("<Key>", on_keypress)

        #create ok button
        ok_button = tk.Button(main_window, text="OK",state="disabled", command=on_ok)
        ok_button.place(x=120, y=100)

        main_window.mainloop()

        if 'cursor' in locals():
            cursor.close()
        if 'cnxn' in locals():
            cnxn.close()
        return selected_value["value"]

    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        if 'cursor' in locals():
            cursor.close()
        if 'cnxn' in locals():
            cnxn.close()
        return

def main(source):
    
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
        arch = source + f'/archive'
        os.makedirs(arch,exist_ok=True)
        image_extensions = ("*.png", "*.jpg", "*.gif")
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(source, ext)))
        #This grabs full image path, so no need to join on source when accessing the file. Can get the filename itself by using os.path.basename(file)
        if len(image_files) == 0:
            raise Exception("No files found")
        if len(image_files) > 1:
            raise Exception("Multiple Images found")
        
        image = image_files[0]
        if os.path.getsize(image) > 256000:
            print(f"Image {os.path.basename(image)} too large. Closing.")
            time.sleep(3)
            raise Exception(f"Image {os.path.basename(image)} too large. Closing.")
        
        logging.info(f"Choosing client")
        client = clientchoose()

        if not client:
            print("Client choice failed")
            time.sleep(3)
            raise Exception("Client choice failed")
        
        logging.info(f"Uploading logo to database for {client}")
        server = 'SQL-SSRS'
        database = 'Appz'
    
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        print("add source argument please")
        time.sleep(5)

