# EEG-sync
Syncing LabRecorder EEG streams for Radcliffe Research Partners.

## Running EEG-sync

To run, make a virutal environment:

`python -m venv virtual_env && source virtual_env/bin/activate`

Then, install the necessary packages by running

`pip install -r requirements.txt`

Each Group i directory should have its corresponding WPI HCI Lab and CSL xdf files in them to run. Each Group directory has a `sync_eegs_i.ipynb` notebook that is used to download the xdf files, sync the EEG streams such that they start at the same UNIX timestamp, and download the synced EEG streams as a .mat file to be used for analysis.

## Notes

Currently, the public facing repo does not have the .xdf files nor the .mat synced EEG files that resulted from this repo. Only WPI and Harvard RRP Fellows have access under Erin Solovey and Chis Micek.
