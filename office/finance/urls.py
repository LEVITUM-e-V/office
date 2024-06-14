from django.urls import path

from . import views

urlpatterns = [
        path("", views.index, name="finance"),
        path("table/", views.finance_table_data, name="finance_table_data"),
        path("insert/", views.finance_insert_entry, name="finance_insert_entry"),
        ]
