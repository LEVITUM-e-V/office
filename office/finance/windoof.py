import requests
from datetime import date, timedelta

LUT_CACHE = {}


class Windoof():
    def __init__(self):
        self.session = requests.session()

    def login(self, access_token):
        self.session.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
                }

    def get_workspace_used_range(
            self, drive_id: str, file_id: str, worksheet_id: str):
        resp = self.session.get(
             f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/"
             f"{file_id}"
             "/workbook/worksheets/"
             f"{worksheet_id}/usedRange"
             )
        resp.raise_for_status()
        return resp.json()

    def get_workspace_range(
            self, drive_id: str, file_id: str, worksheet_id: str, address: str):
        resp = self.session.get(
             f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/"
             f"{file_id}"
             "/workbook/worksheets/"
             f"{worksheet_id}/range(address='{address}')"
             )
        resp.raise_for_status()
        return resp.json()

    def patch_range(self,
                    drive_id: str, file_id: str, worksheet_id: str,
                    address: str, row: list
                    ):
        if address is None:
            raise ValueError('address cannot be null')

        start, end = address.split(':')
        if int(start[1:]) != int(end[1:]):
            raise ValueError('for security reasons only patching of one row is allows. Range is invalid thus')

        resp = self.session.patch(
             f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/"
             f"{file_id}"
             "/workbook/worksheets/"
             f"{worksheet_id}/range(address='{address}')",
             json={
                 'values': [row]
                 }
             )
        resp.raise_for_status()
        return resp.json()

    def insert_row(
            self,
            drive_id: str,
            file_id: str,
            worksheet_id: str,
            values: list,
            start_column='B'
            ):

        if len(start_column) != 1:
            raise ValueError('start column must be a one char')

        table_range = self.get_workspace_used_range(
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
        next_range = self.get_workspace_range(
                drive_id, file_id, worksheet_id,
                address=next_address
                )
        assert next_range['rowCount'] == 1
        assert next_range['cellCount'] == len(values)
        for val_type in next_range['valueTypes'][0]:
            assert val_type == 'Empty'

        patched_range = self.patch_range(
                drive_id, file_id, worksheet_id,
                address=next_address,
                row=values
                )

        return patched_range

    def fetch_children_recursive(self,
                                 drive_id: str,
                                 file_id: str,
                                 max_depth=2
                                 ):

        if max_depth <= 0:
            return {}
        resp = self.session.get(
             f"https://graph.microsoft.com/v1.0/drives/{drive_id}"
             f"/items/{file_id}/children"
                )
        resp.raise_for_status()

        resp = resp.json()

        if resp.get('@odata.null', False):
            return {}

        children = {}

        for child in resp.get('value', []):
            filetype = None
            children_count = 0
            if 'folder' in child:
                filetype = 'folder'
                children_count = child['folder']['childCount']
            elif 'file' in child:
                filetype = child['file']['mimeType']

            children[child['name']] = {
                    'id': child['id'],
                    'type': filetype,
                    'children': self.fetch_children_recursive(drive_id, child['id'], max_depth=max_depth-1) if children_count > 0 else {}
                    }
        return children

    def find_file(self,
                  drive_id: str,
                  folder_id: str,
                  name_prefix: str
                  ):
        resp = self.session.get(
             f"https://graph.microsoft.com/v1.0/drives/{drive_id}"
             f"/items/{folder_id}/children"
                )
        resp.raise_for_status()

        resp = resp.json()

        for child in resp.get('value', []):
            if child['name'].startswith(name_prefix):
                return child

        return None

    def upload_file(self,
                    drive_id: str,
                    folder_id: str,
                    filename: str,
                    content
                    ):
        resp = self.session.put(
             f"https://graph.microsoft.com/v1.0/drives/{drive_id}"
             f"/items/{folder_id}:/{filename}:/content",
             data=content
                )
        resp.raise_for_status()
        return resp.json()

    def _fetch_expenses_folder_LUT(self,
                                   drive_id: str,
                                   file_id: str
                                   ):

        children = self.fetch_children_recursive(
                drive_id,
                file_id
                )

        res = {
                'invoices': {},
                'payment_proof': {},
                'excel_sheet': None,
                }

        for name, child in children.items():
            # this is kinda ugly code and
            # we could do this much simpler and generic
            # but this way we require exact naming
            # of files and exact structure, which is
            # wanted
            if name.startswith('Ausgaben') and \
            child['type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                res['excel_sheet'] = child['id']
            elif child['type'] == 'folder':
                clean_name = {
                        '04 Zahlungsnachweise': 'payment_proof',
                        '02 Rechnungen': 'invoices',
                        }.get(name, None)
                if clean_name is None:
                    continue

                for childchildname, childchild in child['children'].items():
                    month_name = {
                            '01 Januar': '1',
                            '02 Februar': '2',
                            '03 März': '3',
                            '04 April': '4',
                            '05 Mai': '5',
                            '06 Juni': '6',
                            '07 Juli': '7',
                            '08 August': '8',
                            '09 September': '9',
                            '10 Oktober': '10',
                            '11 November': '11',
                            '12 Dezember': '12',
                            }.get(childchildname, None)

                    if month_name is not None:
                        res[clean_name][month_name] = childchild['id']

        return res

    def get_expenses_LUT(self,
                         drive_id: str,
                         file_id,
                         use_cache=True
                         ):
        cache_key = f"{drive_id}{file_id}"
        global LUT_CACHE
        if cache_key not in LUT_CACHE or not use_cache:
            LUT_CACHE[cache_key] = self._fetch_expenses_folder_LUT(drive_id, file_id)
        return LUT_CACHE[cache_key]


def excel_serial_date_to_date(serial_date):
    base_date = date(1899, 12, 30)
    days = int(serial_date)
    return base_date + timedelta(days)


def date_to_excel_serial_date(dt):
    base_date = date(1899, 12, 30)
    delta = dt - base_date
    return delta.days
