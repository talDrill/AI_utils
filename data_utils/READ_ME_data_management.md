
## Manage Data for training models

_Two goals_

### 1) Know when data was last updated

Run script with argument **-lu** or **--last_updated** and it will return 
last update date for each class (action and demography)

If this parameter is entered, no other one is read

### 2) Update data since last update

Run script with parameters **--class_name** (='action' or 'demographic')
and **--input_folder** (json anotation files folder)  
It will automatically build frames and csv accoring to the annotations provided,
from the last update date (it takes into consideration the time 
a task is 'complete' in the cvat)

other parameters: **--output_frames** where to save frames
                  **--csv_folder** where to save csv outputs (append mode)
                    --video_folder where video are stored (default)

If no -lu paramter, all parameters except vidoe_folder are required
