import json
import os
import smtplib
import urllib.request
from email.message import EmailMessage

import pandas as pd

risk = pd.read_csv("reports/stockout_risk.csv")
supp = pd.read_csv("reports/supplier_performance.csv")

critical = risk[risk.status == "Critical"].sort_values("days_of_cover").head(10)
weak = supp[supp.on_time_pct < 80]

lines = [f"Control Tower alert: {int((risk.status == 'Critical').sum())} critical "
         f"and {int((risk.status == 'Reorder now').sum())} reorder-now lines.", ""]
lines.append("Top 10 critical items (stock runs out before a delivery can arrive):")
for _, r in critical.iterrows():
    lines.append(f"- {r.store_name} | {r.product_name}: {r.days_of_cover} days of cover")
if len(weak):
    lines += ["", "Suppliers below 80% on-time:"]
    lines += [f"- {r.supplier_name}: {r.on_time_pct}% on time" for _, r in weak.iterrows()]
message = "\n".join(lines)
print(message)


def send_email(text):
    msg = EmailMessage()
    msg["Subject"] = "Stock-out alert - Control Tower"
    msg["From"], msg["To"] = os.environ["SMTP_USER"], os.environ["EMAIL_TO"]
    msg.set_content(text)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_APP_PASSWORD"])
        smtp.send_message(msg)
    print("\nEmail sent.")


def send_slack(text):
    req = urllib.request.Request(os.environ["SLACK_WEBHOOK_URL"],
                                 data=json.dumps({"text": text}).encode(),
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)
    print("\nSlack message sent.")


if os.environ.get("SMTP_USER") and os.environ.get("EMAIL_TO"):
    send_email(message)
if os.environ.get("SLACK_WEBHOOK_URL"):
    send_slack(message)