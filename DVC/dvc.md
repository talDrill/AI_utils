# DVC - tutorail to using create_dvc_repo.sh
DVC is a data versioning control tool, that let you track changes in data and models. This required to open a git repository for .dvc files. So we create a script that automatically open a git repository from the terminal and accosiate the opened repository the dvc_data repository.
To use the script:
1. Get into Drill_branch/utils/DVC folder: `cd Drill_branch/utils/DVC folder`
2. Run the script with the name of the repository you want to open: `./create_dvc_repo.sh <repo name (for example: demographic_data)>`
These commands will open a repository, make it a submodule of dvc_data repository and push this changes to dvc_data repo.
The last thing you need to do is to push dvc_data commits to Drill_branch repository.