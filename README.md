# SUSI Automations

[![Windows Release](https://github.com/georgi-m-iliev/SUSI_Automations/actions/workflows/release.yaml/badge.svg)](https://github.com/georgi-m-iliev/SUSI_Automations/actions/workflows/release.yaml)

This repository contains my project for automating the enrollment in
electives through the SUSI system of the Sofia University.

NB: This project is for educational purposes only. I do not provide any warranty for the use of this software.
Nor do I take any responsibility for any damage caused by the use of this software.

## Installation of dev environment

1. Clone the repository
2. Install the required packages with `pip install -r requirements.txt`
3. You can run the app with `python main.py`

## Usage

The app is a simple command line interface. You can run it with `python main.py` and follow the instructions.
The workflow is as follows:
1. Log in with your credentials, your session will be saved for the next 10 minutes
2. Provide the start date of the campaign
3. Select the kind of electives you are interested in
4. Select the electives you want to enroll in
5. Confirm your choices
6. The app will try to enroll you in the selected electives
7. If everything goes well, you will receive a confirmation message and be prompted to open a web browser
8. The browser would visualize the POST request that enrolled your electives
9. Check if everything is OK

## Releases

The app is released with the pyinstaller module which builds the app as a standalone executable.
You can find the latest version in the releases section of the repository.

## To Do in the future

* Enroll for multiple kind of electives in one go
* Cover all corner cases and provide feedback

## Contributing

If you want to contribute to the project, you can open an issue or a pull request. I will be happy to discuss any ideas for improvement.
