import requests
from datetime import date, timedelta
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings


def get_workspace_used_range(
        access_token, drive_id: str, file_id: str, worksheet_id: str):
    resp = requests.get(
         f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/"
         f"{file_id}"
         "/workbook/worksheets/"
         f"{worksheet_id}/usedRange",
         headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
                }
         )
    resp.raise_for_status()
    return resp.json()


def excel_serial_date_to_date(serial_date):
    base_date = date(1899, 12, 30)
    days = int(serial_date)
    return base_date + timedelta(days)


@login_required
def finance_table_data(request):
    data = get_workspace_used_range(
            request.session['oidc_access_token'],
            settings.FINANCE_DRIVE_ID,
            settings.FINANCE_SHEET_ID,
            settings.FINANCE_WORKSHEET_ID
            ).get('values')

    for i in range(len(data)):
        if data[i][0] == 'ID':
            data = data[i+1:]
            break

    rows = []
    for row in data:
        if row[1] != '':
            rows.append({
                'id': row[0],
                'date': excel_serial_date_to_date(row[1]).strftime("%d.%m.%Y"),
                'description': row[2],
                'price': row[3],
                'paid_by': row[4]
                })

    return JsonResponse({
        'rows': rows
        })


@login_required
def index(request):
    return render(request, 'finance.html')
