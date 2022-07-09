# coding: utf-8
from datetime import datetime
import json
import logging
from urllib.parse import urlencode

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "SSAM"
DESCRIPTION = "Source for SSAM waste collection."
URL = "https://edpfuture.ssam.se/FutureWeb/SimpleWastePickup/SimpleWastePickup"
TEST_CASES = {
    "SSAM": {"street_address": "Stinavägen 3, Växjö"},
    "Polisen": {"street_address": "Sandgärdsgatan 31, Växjö"},
}
_LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(self, street_address):
        self._street_address = street_address

    def fetch(self):
        response = requests.post(
            "https://edpfuture.ssam.se/FutureWeb/SimpleWastePickup/SearchAdress",
            {"searchText": self._street_address},
        )

        address_data = json.loads(response.text)
        address = None
        if address_data["Succeeded"] and address_data["Succeeded"] is True:
            if address_data["Buildings"] and len(address_data["Buildings"]) > 0:
                address = address_data["Buildings"][0]

        print(address)

        if not address:
            return []

        query_params = urlencode({"address": address})
        response = requests.get(
            "https://edpfuture.ssam.se/FutureWeb/SimpleWastePickup/GetWastePickupSchedule?{}".format(
                query_params
            )
        )
        data = json.loads(response.text)

        entries = []
        for item in data["RhServices"]:
            waste_type = item["WasteType"]
            icon = "mdi:trash-can"
            if waste_type == "Matavfall":
                icon = "mdi:leaf"
            next_pickup = item["NextWastePickup"]

            try:
                next_pickup_date = datetime.fromisoformat(next_pickup).date()
            except ValueError as e:
                # In some cases the date is just a month, so parse this as the
                # first of the month to atleast get something close
                try:
                    next_pickup_date = datetime.strptime(next_pickup, "%b %Y").date()
                except ValueError as e:
                    _LOGGER.warn(f"Failed to parse date {next_pickup} {str(e)}")
                    continue

            entries.append(Collection(date=next_pickup_date, t=waste_type, icon=icon))

        return entries
