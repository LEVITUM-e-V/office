import requests
from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .forms import ExpensesEntryForm
from django.contrib import messages


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


def get_workspace_range(
        access_token, drive_id: str, file_id: str, worksheet_id: str, address: str):
    resp = requests.get(
         f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/"
         f"{file_id}"
         "/workbook/worksheets/"
         f"{worksheet_id}/range(address='{address}')",
         headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
                }
         )
    resp.raise_for_status()
    return resp.json()


def patch_range(access_token,
                drive_id: str, file_id: str, worksheet_id: str,
                address: str, row: list
                ):
    if address is None:
        raise ValueError('address cannot be null')

    start, end = address.split(':')
    if int(start[1:]) != int(end[1:]):
        raise ValueError('for security reasons only patching of one row is allows. Range is invalid thus')

    resp = requests.patch(
         f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/"
         f"{file_id}"
         "/workbook/worksheets/"
         f"{worksheet_id}/range(address='{address}')",
         json={
             'values': [row]
             },
         headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
                }
         )
    resp.raise_for_status()
    return resp.json()


def insert_row(
        access_token,
        drive_id: str,
        file_id: str,
        worksheet_id: str,
        values: list,
        start_column='B'
        ):

    if len(start_column) != 1:
        raise ValueError('start column must be a one char')

    table_range = get_workspace_used_range(
            access_token,
            drive_id, file_id, worksheet_id)
    assert table_range['rowIndex'] == 0

    next_index = None

    for i in range(
            min(
                table_range['rowCount'],
                len(table_range['values']))
            ):
        row = table_range['values'][i]
        if isinstance(row[0], int) and row[1] == '' and row[2] == '':
            next_index = i
            break

    if next_index is None:
        raise ValueError('could not find where to insert the nex row')

    end_column = chr(ord(start_column) + len(values) - 1)
    next_address = f'{start_column}{next_index+1}:{end_column}{next_index+1}'
    next_range = get_workspace_range(
            access_token,
            drive_id, file_id, worksheet_id,
            address=next_address
            )
    assert next_range['rowCount'] == 1
    assert next_range['cellCount'] == len(values)
    for val_type in next_range['valueTypes'][0]:
        assert val_type == 'Empty'

    patched_range = patch_range(
            access_token,
            drive_id, file_id, worksheet_id,
            address=next_address,
            row=values
            )

    return patched_range


def excel_serial_date_to_date(serial_date):
    base_date = date(1899, 12, 30)
    days = int(serial_date)
    return base_date + timedelta(days)


def date_to_excel_serial_date(dt):
    base_date = date(1899, 12, 30)
    delta = dt - base_date
    return delta.days


@login_required
def finance_insert_entry(request):
    if request.method == 'POST':
        form = ExpensesEntryForm(request.POST, user=request.user)
        if form.is_valid():
            values = [
                date_to_excel_serial_date(form.cleaned_data['date']),
                form.cleaned_data['description'],
                float(form.cleaned_data['price']),
                form.cleaned_data['paid_by']
            ]
            resp = insert_row(
                request.session['oidc_access_token'],
                settings.FINANCE_DRIVE_ID,
                settings.FINANCE_SHEET_ID,
                settings.FINANCE_WORKSHEET_ID,
                values,
                start_column='B'
            )

            messages.add_message(request, messages.INFO, f'inserted at {resp["address"]}')
            return redirect('finance')
    else:
        form = ExpensesEntryForm(user=request.user)

    return render(request, 'expenses_entry.html', {'form': form})


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
    for row in reversed(data):
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
