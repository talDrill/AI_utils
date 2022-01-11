
#!/bin/sh

# Check if argument is given
if [ -z "$1" ]; then
    echo -e "No argument is given. Run again with an argument."
    exit 1
fi

# Define all variables
echo "Define variables"
folder=`realpath ../../dvc_data/$1`
parent_folder=`realpath ../../dvc_data/`
dvc_folder="$folder/.dvc"
git_folder="$folder/.git"
remote_folder="/media/data/StoragePath/Datasets/dvc_data/$1"

# Create git repo from command line
echo "Create github repository for $1"
sudo snap install --classic hub
hub create -p Drill-D/$1

# Creating folder for local repo. If exists, skipping this step.
echo "create local repository\n"
if [ -d $folder ]; then
    echo "Directory $folder exists. Skipping creation."
else
    mkdir -p $folder
fi

# Creating the local repo. If .git file exists, skipping this step.
cd $folder
if [ -d $git_folder ]; then
    echo ".git folder exists."
else
    echo "Configure git in $folder"
    pwd
    echo "" >> README.md
    git init
    git add README.md
    git commit -m "first commit"
    git branch -M main
    git remote add origin https://github.com/Drill-D/$1.git
    git push -u origin main
fi

# DVC init. If .dvc file exists, skipping this step.
if [ -d $dvc_folder ]; then
    echo ".dvc folder exists."
else
    echo "Configure dvc in $folder"
    dvc init
    mkdir -p $remote_folder
    dvc remote add -d $1 $remote_folder
    git commit .dvc/config -m "Configure remote storage"
    git push -u origin main
fi

# Made submodule
cd $parent_folder
git submodule add https://github.com/Drill-D/$1.git
git commit -m "Adding $1 as submodule"
git add $1
git commit -m "First commit of $1 as submodule"
git push -u origin main
