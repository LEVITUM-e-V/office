from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .forms import ExpensesEntryForm
from django.contrib import messages
from .windoof import (
        Windoof, date_to_excel_serial_date, excel_serial_date_to_date)


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
            windoof = Windoof()
            windoof.login(request.session['oidc_access_token'])
            resp = windoof.insert_row(
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
    windoof = Windoof()
    windoof.login(request.session['oidc_access_token'])
    data = windoof.get_workspace_used_range(
            settings.FINANCE_DRIVE_ID,
            settings.FINANCE_SHEET_ID,
            settings.FINANCE_WORKSHEET_ID
            ).get('values')

    index_offset = 0
    for i in range(len(data)):
        if data[i][0] == 'ID':
            index_offset = i+1
            data = data[i+1:]
            break

    rows = []
    for id, row in reversed(list(enumerate(data))):
        if row[1] != '':
            rows.append({
                'row_id': index_offset+id+1,
                'id': row[0],
                'date': excel_serial_date_to_date(row[1]).strftime("%d.%m.%Y"),
                'description': row[2],
                'price': row[3],
                'paid_by': row[4]
                })

    return JsonResponse({
        'rows': rows
        })


def generate_filename(prefix: str, entry_id: int, description, price: float, date, file_ending='pdf'):
    formatted_price = f"{price:.2f}".replace('.', ',') + "€"
    formatted_date = date.strftime("%d%m%y")
    entry_id = str(entry_id).zfill(4)
    filename = f"{prefix}_{str(entry_id)}_{description}_{formatted_price}_{formatted_date}.{file_ending}"
    return filename


@login_required
def finance_entry_view(request, row_id: int):
    return render(request, 'finance_entry.html', context={'row_id': row_id})


@require_http_methods(["POST"])
@login_required
def finance_entry_file_upload(request, row_id, file_type):
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'error': 'No file provided'}, status=400)

    prefix = {
        'invoice': 'R',
        'payment_proof': 'Z'
    }.get(file_type)

    if not prefix:
        return JsonResponse({'error': 'Invalid file type'}, status=400)

    windoof = Windoof()
    windoof.login(request.session['oidc_access_token'])
    row = windoof.get_workspace_range(
            settings.FINANCE_DRIVE_ID,
            settings.FINANCE_SHEET_ID,
            settings.FINANCE_WORKSHEET_ID,
            address=f"A{row_id}:E{row_id}"
            ).get('values')[0]

    entry_id = int(row[0])
    date = excel_serial_date_to_date(row[1])
    description = row[2]
    price = row[3]

    lut = windoof.get_expenses_LUT(
            settings.FINANCE_DRIVE_ID,
            settings.FINANCE_EXPENSES_FOLDER_ID
            )

    folder_id = None
    if file_type == "invoice":
        folder_id = lut['invoices'].get(str(date.month))
    elif file_type == "payment_proof":
        folder_id = lut['payment_proof'].get(str(date.month))

    if folder_id is None:
        return JsonResponse({'error': 'Could not find folder where to upload the file to'}, status=500)

    filename = generate_filename(
            prefix,
            entry_id,
            description,
            price,
            date)

    resp = windoof.upload_file(
            settings.FINANCE_DRIVE_ID,
            folder_id,
            filename,
            file.read()
            )

    return JsonResponse({
        file_type: resp
        })


@login_required
@require_http_methods(["GET"])
def finance_entry_data(request, row_id: int):
    windoof = Windoof()
    windoof.login(request.session['oidc_access_token'])
    row = windoof.get_workspace_range(
            settings.FINANCE_DRIVE_ID,
            settings.FINANCE_SHEET_ID,
            settings.FINANCE_WORKSHEET_ID,
            address=f"A{row_id}:E{row_id}"
            ).get('values')[0]

    entry_id = int(row[0])
    date = excel_serial_date_to_date(row[1])
    description = row[2]
    price = row[3]
    paid_by = row[4]

    lut = windoof.get_expenses_LUT(
            settings.FINANCE_DRIVE_ID,
            settings.FINANCE_EXPENSES_FOLDER_ID
            )

    invoices_folder_id = lut['invoices'].get(str(date.month))

    invoice_file = windoof.find_file(
            settings.FINANCE_DRIVE_ID,
            invoices_folder_id,
            f"R_{str(entry_id).zfill(4)}"
            )

    payment_proof_folder_id = lut['payment_proof'].get(str(date.month))
    payment_proof_file = windoof.find_file(
            settings.FINANCE_DRIVE_ID,
            payment_proof_folder_id,
            f"Z_{str(entry_id).zfill(4)}"
            )

    return JsonResponse({
        'values': {
            'id': entry_id,
            'date': date.strftime("%d.%m.%Y"),
            'description': description,
            'price': price,
            'paid_by': paid_by
            },
        'invoice': invoice_file,
        'payment_proof': payment_proof_file,
        })


@login_required
def index(request):
    return render(request, 'finance.html')
