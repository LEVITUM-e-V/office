from django.urls import path

from . import views

urlpatterns = [
        path("", views.index, name="finance"),
        path("table/<int:row_id>/", views.finance_entry_view, name="finance_entry_view"),
        path("api/table/", views.finance_table_data, name="finance_table_data"),
        path("api/table/<int:row_id>/", views.finance_entry_data, name="finance_entry_data"),
        path("api/table/<int:row_id>/<str:file_type>", views.finance_entry_file_upload, name="finance_entry_file_upload"),
        path("insert/", views.finance_insert_entry, name="finance_insert_entry"),
        ]
