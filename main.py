import os
import json
import uuid
from datetime import datetime
from flask import Flask, request, redirect
from bs4 import BeautifulSoup

DRIVERS_FILE = "data/drivers.json"
ARCHIVED_FILE = "data/archived_vehicles.json"

app = Flask(__name__)

# ---------------------------------------------------------------------
# JSON UTILS
# ---------------------------------------------------------------------
def load_json(filepath):
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

def load_drivers():
    return load_json(DRIVERS_FILE)

def save_drivers(drivers):
    save_json(DRIVERS_FILE, drivers)

def load_archived():
    return load_json(ARCHIVED_FILE)

def save_archived(archived):
    save_json(ARCHIVED_FILE, archived)

# ---------------------------------------------------------------------
# MAIN PAGE HTML
# ---------------------------------------------------------------------
def build_main_page_html(drivers, message=None):
    """
    Main page listing:
      - Driver name links to driver_detail
      - Summation of $/mile for each driver's vehicles
      - Remaining Weight, Remaining Length
    No 'deliver' link here anymore.
    """
    html_str = """
    <html>
    <head>
      <title>Car Carrier Manager</title>
      <style>
        body {
          font-family: 'Segoe UI', Tahoma, sans-serif;
          margin: 0; padding: 0;
          background-color: #f7f9fc;
        }
        header {
          background-color: #343a40;
          color: #ffffff;
          padding: 1rem;
          text-align: center;
        }
        h1 {
          margin: 0; 
          font-weight: 400;
        }
        .container {
          max-width: 900px;
          margin: 2rem auto;
          background-color: #ffffff;
          padding: 2rem;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        .alert {
          background-color: #d4edda; /* light green */
          color: #155724;
          padding: 10px;
          margin-bottom: 1rem;
          border: 1px solid #c3e6cb;
          border-radius: 4px;
        }
        .nav-links {
          margin-bottom: 1rem;
        }
        .nav-links a {
          display: inline-block;
          margin-right: 10px;
          padding: 8px 14px;
          background-color: #007bff;
          color: #ffffff;
          text-decoration: none;
          border-radius: 4px;
        }
        .nav-links a.secondary {
          background-color: #6c757d;
        }
        table.driver-table {
          width: 100%;
          border-collapse: collapse;
        }
        .driver-table th {
          background-color: #f1f1f1;
          text-align: left;
          padding: 10px;
        }
        .driver-table td {
          border-bottom: 1px solid #ddd;
          padding: 10px;
        }
        .action-button {
          display: inline-block;
          margin-right: 6px;
          padding: 6px 12px;
          background-color: #28a745;
          color: #ffffff;
          text-decoration: none;
          border-radius: 4px;
          font-size: 0.85rem;
        }
        .action-button.secondary {
          background-color: #17a2b8;
        }
        .action-button.danger {
          background-color: #dc3545;
        }
        footer {
          text-align: center;
          margin: 2rem 0;
          color: #888;
        }
      </style>
    </head>
    <body>
      <header>
        <h1>Car Carrier Manager</h1>
      </header>

      <div class="container">
        <div class="msg-placeholder"></div>

        <div class="nav-links">
          <a href="/add_driver">Add Driver</a>
          <a href="/archived" class="secondary">View Archived</a>
          <a href="/calculator" class="secondary">Calculator</a>
        </div>

        <h2>All Drivers</h2>
        <table class="driver-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Name</th>
              <th>Loaded</th>
              <th>Rem Wt</th>
              <th>Sum($/mi)</th>
              <th>Rem Len</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
          </tbody>
        </table>
      </div>

      <footer>&copy; 2025 Car Carrier Manager | Offline Edition</footer>
    </body>
    </html>
    """
    soup = BeautifulSoup(html_str, "html.parser")

    # If there's a message, show it in an alert
    if message:
        alert_div = soup.new_tag("div", **{"class": "alert"})
        alert_div.string = message
        container_div = soup.find("div", {"class": "msg-placeholder"})
        container_div.insert_after(alert_div)

    tbody = soup.find("tbody")

    for i, d in enumerate(drivers):
        loaded = len(d["vehicles"])
        cap = d["vehicle_capacity"]

        # Remaining Weight
        current_weight = sum(v["weight"] for v in d["vehicles"])
        rem_wt = d["allowed_cargo_weight"] - current_weight

        # Sum($/mi)
        total_dollar_mi = sum(v.get("dollar_per_mile", 0.0) for v in d["vehicles"])

        # Remaining Length
        used_length = sum(v["length"] for v in d["vehicles"]) + (loaded * d["safe_distance"])
        rem_len = d["carrier_length_limit"] - used_length
        if rem_len < 0:
            rem_len = 0

        row = soup.new_tag("tr")

        # index
        td_index = soup.new_tag("td")
        td_index.string = str(i)
        row.append(td_index)

        # name (link)
        td_name = soup.new_tag("td")
        link_detail = soup.new_tag("a", href=f"/driver_detail?index={i}")
        link_detail.string = d["name"]
        td_name.append(link_detail)
        row.append(td_name)

        # loaded
        td_loaded = soup.new_tag("td")
        td_loaded.string = f"{loaded}/{cap}"
        row.append(td_loaded)

        # remaining weight
        td_remwt = soup.new_tag("td")
        td_remwt.string = f"{rem_wt} lbs"
        row.append(td_remwt)

        # sum($/mi)
        td_sum_dpm = soup.new_tag("td")
        td_sum_dpm.string = str(round(total_dollar_mi, 2))
        row.append(td_sum_dpm)

        # remaining length
        td_remlen = soup.new_tag("td")
        td_remlen.string = f"{round(rem_len,2)} ft"
        row.append(td_remlen)

        # actions
        td_actions = soup.new_tag("td")

        # Edit link
        link_edit = soup.new_tag("a", href=f"/edit_driver?index={i}", **{"class": "action-button secondary"})
        link_edit.string = "Edit"
        td_actions.append(link_edit)

        # Delete link
        link_delete = soup.new_tag("a", href=f"/delete_driver?index={i}", **{"class": "action-button danger"})
        link_delete.string = "Delete"
        td_actions.append(link_delete)

        # Add Vehicle
        link_vehicle = soup.new_tag("a", href=f"/add_vehicle?driver_index={i}", **{"class": "action-button"})
        link_vehicle.string = "Add Vehicle"
        td_actions.append(link_vehicle)

        row.append(td_actions)
        tbody.append(row)

    return str(soup)

# ---------------------------------------------------------------------
# ARCHIVED PAGE HTML
# ---------------------------------------------------------------------
def build_archived_page_html(archived):
    """
    Show all data from each archived vehicle, not just name & weight.
    We'll create a table with all relevant fields.
    """
    html = """
    <html>
    <head>
      <title>Archived Vehicles</title>
      <style>
        body {
          font-family: 'Segoe UI', Tahoma, sans-serif;
          margin: 0; padding: 0;
          background-color: #f7f9fc;
        }
        header {
          background-color: #343a40;
          color: #ffffff;
          padding: 1rem;
          text-align: center;
        }
        h1 {
          margin: 0; 
          font-weight: 400;
        }
        .container {
          max-width: 900px;
          margin: 2rem auto;
          background-color: #ffffff;
          padding: 2rem;
          box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        a.button {
          display: inline-block;
          margin-bottom: 1rem;
          padding: 8px 14px;
          background-color: #007bff;
          color: #ffffff;
          text-decoration: none;
          border-radius: 4px;
        }
        table {
          width: 100%;
          border-collapse: collapse;
        }
        th, td {
          padding: 10px;
          border-bottom: 1px solid #ddd;
          text-align: left;
        }
        th {
          background-color: #f1f1f1;
        }
        footer {
          text-align: center;
          margin: 2rem 0;
          color: #888;
        }
      </style>
    </head>
    <body>
      <header>
        <h1>Archived Vehicles</h1>
      </header>

      <div class="container">
        <a href="/" class="button">Back to Home</a>
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Make/Model/Year</th>
              <th>Weight</th>
              <th>Height</th>
              <th>Length</th>
              <th>Distance</th>
              <th>$/mi</th>
              <th>Comment</th>
              <th>Delivered At</th>
            </tr>
          </thead>
          <tbody>
          </tbody>
        </table>
      </div>

      <footer>&copy; 2025 Car Carrier Manager | Offline Edition</footer>
    </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    tbody = soup.find("tbody")

    for i, v in enumerate(archived):
        row = soup.new_tag("tr")

        td_index = soup.new_tag("td")
        td_index.string = str(i)
        row.append(td_index)

        td_mm = soup.new_tag("td")
        td_mm.string = v.get("make_model_year", "")
        row.append(td_mm)

        td_weight = soup.new_tag("td")
        td_weight.string = str(v.get("weight", ""))
        row.append(td_weight)

        td_height = soup.new_tag("td")
        td_height.string = str(v.get("height", ""))
        row.append(td_height)

        td_length = soup.new_tag("td")
        td_length.string = str(v.get("length", ""))
        row.append(td_length)

        td_dist = soup.new_tag("td")
        td_dist.string = str(v.get("distance", ""))
        row.append(td_dist)

        td_dpm = soup.new_tag("td")
        td_dpm.string = str(v.get("dollar_per_mile", 0.0))
        row.append(td_dpm)

        td_comment = soup.new_tag("td")
        td_comment.string = v.get("comment", "")
        row.append(td_comment)

        td_del = soup.new_tag("td")
        td_del.string = v.get("delivered_at", "Unknown")
        row.append(td_del)

        tbody.append(row)

    return str(soup)

# ---------------------------------------------------------------------
# HOME ROUTE
# ---------------------------------------------------------------------
@app.route("/")
def home():
    msg = request.args.get("msg", "")
    drivers = load_drivers()
    page_html = build_main_page_html(drivers, message=msg)
    return page_html

# ---------------------------------------------------------------------
# ARCHIVED ROUTE
# ---------------------------------------------------------------------
@app.route("/archived")
def archived_page():
    arch = load_archived()
    page_html = build_archived_page_html(arch)
    return page_html

# ---------------------------------------------------------------------
# DRIVER DETAIL (Now includes DELIVER button for each vehicle)
# ---------------------------------------------------------------------
@app.route("/driver_detail")
def driver_detail():
    drivers = load_drivers()
    idx = int(request.args.get("index", "-1"))
    if idx < 0 or idx >= len(drivers):
        return "<h1>Invalid driver index</h1><p><a href='/'>Back</a></p>"
    driver = drivers[idx]

    total_dpm = sum(v.get("dollar_per_mile", 0.0) for v in driver["vehicles"])

    html = f"""
    <html>
    <head>
      <title>Driver Detail</title>
      <style>
        body {{
          font-family: 'Segoe UI', Tahoma, sans-serif;
          background-color: #f7f9fc;
          margin: 0; padding: 0;
        }}
        .container {{
          max-width: 800px;
          margin: 2rem auto;
          background-color: #fff;
          padding: 2rem;
          box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        h1 {{
          font-weight: 400;
        }}
        table {{
          width: 100%;
          border-collapse: collapse;
        }}
        th, td {{
          padding: 10px;
          border-bottom: 1px solid #ddd;
          text-align: left;
        }}
        th {{
          background-color: #f1f1f1;
        }}
        a.button {{
          display: inline-block;
          margin-top: 1rem;
          padding: 8px 14px;
          background-color: #007bff;
          color: #ffffff;
          text-decoration: none;
          border-radius: 4px;
        }}
        a.del-button {{
          background-color: #dc3545;
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Driver Detail: {driver['name']}</h1>
        <p>Capacity: {driver['vehicle_capacity']}, Allowed Weight: {driver['allowed_total_weight']}, 
           Remaining Wt: {driver['allowed_cargo_weight'] - sum(v["weight"] for v in driver["vehicles"])} lbs</p>
        <p><strong>Sum of $/mi: {round(total_dpm,2)}</strong></p>

        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Vehicle</th>
              <th>Weight</th>
              <th>Height</th>
              <th>Length</th>
              <th>Distance</th>
              <th>$/mi</th>
              <th>Comment</th>
              <th>Deliver</th>
            </tr>
          </thead>
          <tbody>
    """
    for i, v in enumerate(driver["vehicles"]):
        dpm_val = v.get("dollar_per_mile", 0.0)
        # We'll add a link: /deliver_vehicle?driver_index=xxx&veh_index=xxx
        deliver_link = f"/deliver_vehicle?driver_index={idx}&veh_index={i}"
        html += f"""
          <tr>
            <td>{i}</td>
            <td>{v['make_model_year']}</td>
            <td>{v['weight']}</td>
            <td>{v['height']}</td>
            <td>{v['length']}</td>
            <td>{v['distance']}</td>
            <td>{round(dpm_val,2)}</td>
            <td>{v['comment']}</td>
            <td><a href="{deliver_link}" class="button del-button">Deliver</a></td>
          </tr>
        """

    html += """
          </tbody>
        </table>
        <a href="/" class="button">Back</a>
      </div>
    </body>
    </html>
    """
    return html

# ---------------------------------------------------------------------
# CALCULATOR
# ---------------------------------------------------------------------
@app.route("/calculator", methods=["GET", "POST"])
def calculator():
    if request.method == "GET":
        form_html = """
        <html>
        <head>
          <title>Calculator</title>
          <style>
            body {
              font-family: 'Segoe UI', Tahoma, sans-serif;
              background-color: #f7f9fc;
              margin: 0; padding: 0;
            }
            .container {
              max-width: 600px;
              margin: 2rem auto;
              background: #fff;
              padding: 2rem;
              box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            label { display: block; margin: 1rem 0 0.3rem; }
            input {
              width: 100%;
              padding: 0.5rem;
              margin-bottom: 1rem;
              border: 1px solid #ccc;
              border-radius: 4px;
            }
            button {
              background-color: #007bff;
              color: #fff;
              border: none;
              padding: 0.8rem 1.2rem;
              border-radius: 4px;
              cursor: pointer;
            }
            a.button {
              background-color: #6c757d;
              margin-top: 1rem;
              display: inline-block;
              padding: 8px 14px;
              color: white;
              text-decoration: none;
              border-radius: 4px;
            }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>Distance Calculator</h1>
            <form method="POST">
              <label>Miles (to convert to kilometers)</label>
              <input type="number" step="any" name="miles" placeholder="e.g. 100.5">

              <label>Feet (to convert to meters)</label>
              <input type="number" step="any" name="feet" placeholder="e.g. 10">

              <label>Inches (to convert to meters)</label>
              <input type="number" step="any" name="inches" placeholder="e.g. 4">

              <button type="submit">Calculate</button>
            </form>
            <div class="results"></div>
            <p><a href="/" class="button">Back</a></p>
          </div>
        </body>
        </html>
        """
        return form_html
    else:
        miles_str = request.form.get("miles", "").strip()
        feet_str = request.form.get("feet", "").strip()
        inches_str = request.form.get("inches", "").strip()

        result_msg = []
        try:
            if miles_str:
                miles_val = float(miles_str)
                km_val = miles_val * 1.60934
                result_msg.append(f"{miles_val} miles = {round(km_val,2)} km")
        except:
            pass

        try:
            if feet_str or inches_str:
                ft_val = float(feet_str) if feet_str else 0.0
                in_val = float(inches_str) if inches_str else 0.0
                total_inches = ft_val*12 + in_val
                meters_val = total_inches * 0.0254
                result_msg.append(f"{ft_val} ft {in_val} in = {round(meters_val,2)} m")
        except:
            pass

        results_html = "<br>".join(result_msg) if result_msg else "No valid input."

        form_html = f"""
        <html>
        <head>
          <title>Calculator</title>
          <style>
            body {{
              font-family: 'Segoe UI', Tahoma, sans-serif;
              background-color: #f7f9fc;
              margin: 0; padding: 0;
            }}
            .container {{
              max-width: 600px;
              margin: 2rem auto;
              background: #fff;
              padding: 2rem;
              box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            label {{ display: block; margin: 1rem 0 0.3rem; }}
            input {{
              width: 100%;
              padding: 0.5rem;
              margin-bottom: 1rem;
              border: 1px solid #ccc;
              border-radius: 4px;
            }}
            button {{
              background-color: #007bff;
              color: #fff;
              border: none;
              padding: 0.8rem 1.2rem;
              border-radius: 4px;
              cursor: pointer;
            }}
            a.button {{
              background-color: #6c757d;
              margin-top: 1rem;
              display: inline-block;
              padding: 8px 14px;
              color: white;
              text-decoration: none;
              border-radius: 4px;
            }}
            .results {{
              background-color: #d4edda;
              color: #155724;
              padding: 10px;
              border: 1px solid #c3e6cb;
              border-radius: 4px;
              margin-top: 1rem;
            }}
          </style>
        </head>
        <body>
          <div class="container">
            <h1>Distance Calculator</h1>
            <form method="POST">
              <label>Miles (to convert to kilometers)</label>
              <input type="number" step="any" name="miles" value="{miles_str}">

              <label>Feet (to convert to meters)</label>
              <input type="number" step="any" name="feet" value="{feet_str}">

              <label>Inches (to convert to meters)</label>
              <input type="number" step="any" name="inches" value="{inches_str}">

              <button type="submit">Calculate</button>
            </form>
            <div class="results">{results_html}</div>
            <p><a href="/" class="button">Back</a></p>
          </div>
        </body>
        </html>
        """
        return form_html

# ---------------------------------------------------------------------
# DELIVER VEHICLE
# ---------------------------------------------------------------------
@app.route("/deliver_vehicle")
def deliver_vehicle():
    """
    Moved from main page to driver detail.
    This route finalizes the delivery, moves vehicle to archived_vehicles with all fields.
    """
    drivers = load_drivers()
    archived = load_archived()
    driver_index = int(request.args.get("driver_index", "-1"))
    veh_index = int(request.args.get("veh_index", "-1"))

    if driver_index < 0 or driver_index >= len(drivers):
        return redirect("/?msg=Invalid+driver+index")
    driver = drivers[driver_index]

    if veh_index < 0 or veh_index >= len(driver["vehicles"]):
        return redirect("/?msg=Invalid+vehicle+index")

    vehicle = driver["vehicles"].pop(veh_index)
    vehicle["delivered_at"] = datetime.now().isoformat()

    # store ALL fields in archived
    archived.append(vehicle)
    save_archived(archived)
    save_drivers(drivers)

    return redirect(f"/driver_detail?index={driver_index}")

# ---------------------------------------------------------------------
# STARTUP
# ---------------------------------------------------------------------
def ensure_data_files():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(DRIVERS_FILE):
        with open(DRIVERS_FILE, "w") as f:
            f.write("[]")
    if not os.path.exists(ARCHIVED_FILE):
        with open(ARCHIVED_FILE, "w") as f:
            f.write("[]")

if __name__ == "__main__":
    ensure_data_files()
    app.run(debug=True, port=5000)