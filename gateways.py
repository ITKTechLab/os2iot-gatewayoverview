# %%
import requests
import json
import os
import re
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import utm
load_dotenv(override=True)

# %%
base_url = os.getenv('os2iot_BASE_URL')
os2iot_url = os.getenv('os2iot_URL')
chirpstack_url = os.getenv('chirpstack_URL')
os2iot_api = os.getenv('os2iot_api')
org_id = os.getenv('os2iot_org_id')
kerlink_password = os.getenv('kerlink_password')
directory = os.getenv('directory')
wmc_base_url = os.getenv('wmc_base_url')

directory = directory if os.path.isdir(directory) else os.getcwd()
url = f"{base_url}/chirpstack/gateway?organizationId={org_id}&limit=100000&offset=0"

headers = {
  'X-API-KEY': os2iot_api
}

response = requests.get(url, headers=headers)

data = json.loads(response.text)

# %%
for item in data['resultList']:
    location = item.get('location', {})
    item['latitude'] = location.get('latitude')
    item['longitude'] = location.get('longitude')

for item in data['resultList']:
    tags = item.get('tags', {})
    item['Phone'] = tags.get('Phone')
    item['MAC'] = tags.get('MAC')
    item['IP'] = tags.get('IP')
    item['SNMP'] = tags.get('SNMP')

gateway_df = pd.DataFrame(data.get('resultList', []))[['gatewayId',
                                                       'name',
                                                       'Phone',
                                                       #'operationalResponsibleName',
                                                       #'rxPacketsReceived',
                                                       #'txPacketsEmitted',
                                                       #'modelName',
                                                       #'antennaType',
                                                       'placement',
                                                       'latitude',
                                                       'longitude',
                                                       'MAC',
                                                       'IP',
                                                       'SNMP',
                                                       'lastSeenAt',
                                                       'status']]

gateway_df = gateway_df.rename(columns={'gatewayId': 'gatewayEUI',
                                        'name': 'gateway_name'})

today_str = datetime.today().strftime("%Y-%m-%d")

gateway_df['lastSeenAt'] = pd.to_datetime(gateway_df['lastSeenAt'])
gateway_df['lastSeenAt'] = gateway_df['lastSeenAt'].dt.date

gateways_online = (gateway_df['lastSeenAt'] == pd.to_datetime(today_str).date()).sum()

gateway_df['lastSeenAt'] = gateway_df['lastSeenAt'].apply(
    lambda date: f"<span style='color:green'>{date}</span>" if str(date) == today_str else f"<span style='color:red'>{date}</span>"
)

today_str = f"{today_str} - {gateways_online} gateways are currently online"

gateway_df['map'] = gateway_df.apply(
    lambda item: '🧭️' if pd.isna(item['latitude']) or item['latitude'] == 0 else f'<a href="https://skraafoto.dataforsyningen.dk/?center={utm.from_latlon(item["latitude"], item["longitude"])[0]:.2f}%2C{utm.from_latlon(item["latitude"], item["longitude"])[1]:.2f}" title="{item["latitude"]}, {item["longitude"]}" target="_blank">🗺</a>', axis=1
)
gateway_df.drop(columns=['latitude', 'longitude'], inplace=True)

gateway_df['placement'] = gateway_df['placement'].apply(
    lambda p: f"{p} &#x1F3E2;" if p == "INDOORS" else f"{p} &#127780;&#65039;"
)

gateway_df = gateway_df.sort_values(by=['gateway_name'],key=lambda col: col.str.lower())

gateway_df['OS2IOT'] = gateway_df.apply(lambda row: f"<a href=\"{os2iot_url}/gateways/gateway-detail/{row['gatewayEUI']}\" target=\"_blank\">{row['gatewayEUI'][-4:]}</a>", axis=1)
gateway_df['WMC'] = gateway_df.apply(lambda row: f"<a href=\"https://wmc.wanesy.com/gateways/176/{row['gatewayEUI']}\" target=\"_blank\">{row['gatewayEUI'][-4:]}</a>", axis=1)
gateway_df['Chirpstack'] = gateway_df.apply(lambda row: f"<a href=\"{chirpstack_url}{row['gatewayEUI']}\" target=\"_blank\">{row['gatewayEUI'][-4:]}</a>", axis=1)

# Works with WinSCP
gateway_df['SSH'] = gateway_df.apply(
    lambda row: (
        f"<a href=\"ssh:root@{row['IP']}\" target=\"_blank\">{row['gatewayEUI'][-4:]}</a>"
        if isinstance(row['IP'], str) and re.fullmatch(r'(?:\d{1,3}\.){3}\d{1,3}', row['IP'])
        else ""
    ),
    axis=1
)

gateway_df['HTTP'] = gateway_df.apply(
    lambda row: (
        f"<a href=\"http://{row['IP']}\" target=\"_blank\">{row['gatewayEUI'][-4:]}</a>"
        if isinstance(row['IP'], str) and re.fullmatch(r'(?:\d{1,3}\.){3}\d{1,3}', row['IP'])
        else ""
    ),
    axis=1
)

gateway_df['Phone'] = gateway_df['Phone'].apply(
    lambda phone: (
        f'<a href="sms:{phone}?&body=[admin:{kerlink_password}] [reboot] system/reboot" target="_blank">{phone}</a>'
        if isinstance(phone, str) and re.fullmatch(r'\+?\d{10,}', phone)
        else "&#x1F4F5;"
    )
)

# %%
html_string = '''
<!doctype html>
<html lang="en">
  <head>
    <title>LoRaWAN Gateways - {today_str}</title>
    <!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@3.4.1/dist/css/bootstrap.min.css" integrity="sha384-HSMxcRTRxnN+Bdg0JdbxYKrThecOKuH5zCYotlSAcp1+c8xmyTe9GYg1l9a69psu" crossorigin="anonymous">
    <!-- Optional theme -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@3.4.1/dist/css/bootstrap-theme.min.css" integrity="sha384-6pzBo3FDv/PJ8r2KRkGHifhEocL+1X2rVCTTkUfGk7/0pbek5mMa1upzvWbrUbOZ" crossorigin="anonymous">
    <!-- Latest compiled and minified JavaScript -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@3.4.1/dist/js/bootstrap.min.js" integrity="sha384-aJ21OjlMXNL5UyIl/XNwTMqvzeRMZH2w8c5cRVpzpU8Y5bApTppSuUkhZXN0VxHd" crossorigin="anonymous"></script>

    <script src="https://cdn.jsdelivr.net/npm/table-sort-js/table-sort.min.js"></script>

    <style>
    table {{
        white-space: nowrap;
        overflow: hidden;
    }}
    </style>
  </head>
  <body>
    <div class="container-fluid">
    <h1>LoRaWAN Gateways - {today_str}</h1>
    {table}
    </div>
  </body>
</html>
'''

if(gateway_df.empty):
    print("Error: No gateways found.")
else:
  with open(directory + '/gateways.html', 'w') as f:
    f.write(html_string.format(table=gateway_df.to_html(bold_rows=True,
                                                        index=False, 
                                                        justify='left',
                                                        escape=False, 
                                                        classes='table table-striped table-bordered table-sort table-arrows table-hover'),
                                                        today_str = today_str))
#gateway_df.to_html(os.getcwd() + '/gateways.html', encoding='utf-8', bold_rows=True, index=False, justify='left', escape=False)

# %%
gateway_df


