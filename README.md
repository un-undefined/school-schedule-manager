This schedule manager is meant for my school's schedule system, and for Windows only.
On first download, this program will:
 - Create a `config.json` file in `C:\Users\<USER>\AppData\Local`, or `%localappdata%`.
     - This file can be directly modified if it is required.
     - If you change it to be illegal / incorrect, the program will likely crash.
     - It is recommended to edit the configuration in the built-in style or class editor.
 - Add a .bat file to `C:\Users\thoug\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`
     - This causes it to open on computer startup.
     - If you do not want this, you can delete `school_schedule_manager_startup.bat` from that folder.

The built-in configuration editor is better for modifying settings than directly changing the `config.json` file through a text editor or from the program itself (Edit Configuration File)
The configuration settings includes:
 - Style Editor (can change most UI colors)
 - Class Editor (can change accent color, icon, name, and period)
 - Special Day Editor (can change certain short or no-school days, and the school start and end dates)

This software is licensed under the MIT License.
