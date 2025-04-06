# Car Carrier Manager 🚚

A simple offline web app to manage car carrier logistics, built with Python and Flask.

## Features

- Add/edit/delete drivers and vehicles
- Tracks:
  - Remaining cargo weight
  - Remaining length
  - Dollar-per-mile totals
- Delivery tracking and archiving
- Auto-validates vehicle limits (weight, height, length)
- In-browser calculator: miles → km and ft/in → meters
- Clean, responsive HTML UI using BeautifulSoup

## Run the App

### Requirements

Make sure you have Python 3 installed.

Install dependencies:

```bash
pip install -r requirements.txt

to start the app
python main.py

then open http://localhost:5000 in your browser.
