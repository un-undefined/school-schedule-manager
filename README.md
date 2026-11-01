## Year Code for 2026-2027 School Year:
```text
Year:2026;Adv:3;Limit:C286;NoS:CFD9EBECF0FDGFGGGHI5I6I9IAIBIC010I262728292A4855565758597F;Short:CHFCG9GAGDGEHAI40D0J103C50848586
```

## Important Setup Info
This schedule manager is meant for my school's schedule system, and for Windows only.
On first run, this program will:
 - Create a `config.json` file in `C:\Users\<USER>\AppData\Local\WHSSchoolScheduleManager`, or `%localappdata%\WHSSchoolScheduleManager`.
     - This file can be directly modified if it is required.
     - If you change it to be illegal / incorrect, the program will likely crash.
     - It is recommended to edit the configuration in the built-in style or class editor.
     - The direct modification is possible in the UI, and it does check for JSON syntax errors, but not date formatting and parsing errors.
 - Create a `default.config.json` file in the same directory.
     - Refrain from editing this file.
 - [Optional] Add a shortcut to `C:\Users\<USER>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`.
     - This causes it to open on computer startup.
     - If you do not want this, you can delete it from that folder, or do not check the box in the Setup.
 - [Optional] Add a desktop shortcut to open the program.

The built-in configuration editor is better for modifying settings than directly changing the `config.json` file through a text editor or from the program itself (Edit Configuration File)
The configuration settings includes:
 - Style Editor (can change most UI colors)
 - Class Editor (can change accent color, icon, name, and period)
 - Special Day Editor (can import a savecode for that year specifically)

To directly change the special days, like school start, school end, shortened days, and no-school days, modify the configuration file directly.

Inno Setup is used to install the app on your computer easily.

Please ignore my horrible coding. It works.

This software is licensed under the MIT License.
Read the `LICENSE` file for additional information.
