# GImages
# Goods in image import and part details display

This program was originally conceived as a way to provide the Goods In team easy access to images for the parts they are accepting into the warehouse, allowing them to see any obvious issues or faults with the items more easily. It has since grown into a full item checker, giving the user a full set of information regarding the item, including current stock, current allocations, current bin, the default supplier, weight and volume. This allows the Goods In team to accept and move the stock quickly.

The application has 4 options - in default mode, it automatically switches to the "Display" option, but if the shortcut used has an additional argument, and that argument is "maint", all four options will be given.

1. Maintenance. The user must select a client and then find a part, either by providing the barcode, the SKU or by selecting a SKU from a drop down menu. This then shows the images and details for the parts, and allows the user to delete the image shown.
2. Display. This is the same as the Maintenance screen, except the option to delete the image has been removed.
3. Import. Allows the user to choose a client and a "separator". The folder imported from is based on the client chosen, the SKU associated is based on the filename of the image file, and the separator allows multiple images for the same SKU. This then imports the images into the system for the client specified.
4. Create Folder. This creates the folder structure needed for the Import option above. The base folder is hard coded, and the folder name is based off the site and database name of the client.

At time of writing, this is not in use as we have only received a few test images from clients. In addition, to be 100% useful, this needs to be able to run on our handheld scanners - there is an SSRS report that duplicates the "Display" screen that can work, but not yet fully deployed.
