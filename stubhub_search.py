import sys

# module imports
sys.path.append('./modules')
import tools
import push

push_instance = push.Push(calling_function="TicketSearch")

# package imports
import datetime
import json
import requests
from bs4 import BeautifulSoup
import threading
import time


class TicketSearch:

    def __init__(self, url, name="None given", debug = False,
                 price_limit=250, upper_level_price_limit=100, loop_sleep=120):
        self.url = url
        self.listing_name = name
        self.debug = debug
        self.listings = dict()
        self.current_listings = list()
        self.found_listings = list()
        self.upper_level_price_limit = upper_level_price_limit
        self.price_limit = price_limit
        self.loop_sleep = loop_sleep
        self.loop_sleep_interval = 2

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value: bool):
        self._debug = value

    @property
    def price_limit(self):
        return self._price_limit

    @price_limit.setter
    def price_limit(self, value):
        if value <= 0:
            raise ValueError(f"Provide a positive price")
        self._price_limit = value

    def __str__(self):
        return f"{self.listing_name}"

    def __repr__(self):
        return f"{self.listing_name}"

    def get_listings(self, url):

        # Get raw listings json from site
        print(f"Current price limit: {self.price_limit}\n")
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        elements_with_class = soup.find(id="index-data")
        text = json.loads(elements_with_class.getText().split('\r\n')[1].lstrip())
        return text

    def process_site_listings(self, site_listings, price_limit=225):

        upper_level_price_limit = 100
        print(f"Starting search with price limit of {price_limit}")
        self.found_listings.clear()
        new_listings = list()

        for site_listing in site_listings:
            listing_id = site_listing['id']
            price = site_listing['rawPrice']
            reported_quantity = site_listing.get('availableTickets')
            available_quantities = list()
            for available_quantity in site_listing['availableQuantities']:
                available_quantities.append(available_quantity)
            section_header = str(site_listing['section'])[0]
            section = str(site_listing['section'])
            row = site_listing['row']

            if ((reported_quantity == 2 or 2 in available_quantities) and
                    (price <= price_limit and section_header != "3" and row != "GA") or
                    price < upper_level_price_limit):
                self.found_listings.append(listing_id)
                if self.listings.get(listing_id) is None:
                    new_listings.append(listing_id)
                    msg = (f"Section: {section} "
                           f"Row:{row}\n"
                           f"Price:{price}\n"
                           f"Listing ID: {listing_id}\n"
                           f"Price limit: {price_limit}\n"
                           f"Available quantities: {available_quantities}\n")
                    msg += f"Time: {datetime.datetime.now().strftime('%Y%m%d %H:%M:%S')}\n\n\n"
                    self.listings[listing_id] = msg
                    push_instance.logger_instance.warning(msg)
                    push_instance.push(f"New listing:\n{msg}", title="Tickets")
                else:
                    if self.debug:
                        push_instance.logger_instance.info(f"Skipping listing ID: {listing_id}")
                    pass
            else:
                if self.debug:
                    print(f"Skipped SectionHeader: {section_header}, Section:{section}, row:{row} "
                          f"Price:{price}, AvailableQuantities:{available_quantities}, "
                          f"ReportedQuantity:{reported_quantity}")
                    print("\n")
                pass

        return new_listings

    def search_listings(self):

        site_json = self.get_listings(self.url)
        site_listings = site_json['grid']['items']

        new_listings = self.process_site_listings(site_listings, price_limit=self.price_limit)

        # Log if no new listings found
        if len(new_listings) == 0:
            msg = "No new listings found"
            msg += f" {datetime.datetime.now().strftime('%Y%m%d %H:%M:%S')}"
            push_instance.logger_instance.warning(msg)
            # push_instance.push(msg, title="Tickets")

        # If no listings exist at current price level, raise the limit by $5
        if len(self.listings) == 0:
            price_limit_increase_msg = f"No listings at current price, raising price limit from {self.price_limit} to "
            self.price_limit += 5
            price_limit_increase_msg += f"{self.price_limit}"
            push_instance.push(price_limit_increase_msg, title="Tickets")
            push_instance.logger_instance.warning(f"{price_limit_increase_msg}")

        # Go through previously reported listings to make sure they are still available
        deleted_listings = list()
        for listing in self.listings.keys():
            if listing in self.found_listings:
                # push_instance.logger_instance.info(f"Old listing {listing} still available")
                pass
            else:
                push_instance.logger_instance.warning(f"Old listing {listing} no longer available")
                deleted_listing_msg = f"Listing no longer available:\n{self.listings[listing]}"
                push_instance.logger_instance.warning(deleted_listing_msg)
                push_instance.push(deleted_listing_msg, title="Tickets")
                deleted_listings.append(listing)

        # Remove recently deleted listings from list of known available listings
        for listing in deleted_listings:
            self.listings.pop(listing)

    def report_listings(self):
        push_instance.push(f"\nListings report:\n")
        if len(self.listings) == 0:
            for listing in self.listings.keys():
                push_instance.push(self.listings[listing])
                push_instance.push(f"\n")
        else:
            push_instance.push(f"\nNo listings at current price limit ({self.price_limit})\n")

    def slack_thread(self, calling_function="ListingSearchSlack"):
        # ADD A ROW IN THE Slack TABLE OF THE Process Database. Use values (calling_function, 0)
        print(f"Read slack thread initiated for {str(self)} listing search\n")
        slack_instance = push.Push(calling_function=calling_function)
        while True:
            update_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            slack_text = slack_instance.read_slack()
            if slack_text != "":
                slack_instance.logger_instance.info(f"Slack text received at ({update_time}):{slack_text}.")
                slack_instance.push(f"Received slack request: {slack_text}")
                self.process_slack_text(slack_text)
            time.sleep(5)

    def process_slack_text(self, text):
        if text.upper()[0:2] == "L:":
            if text[2:].isdigit():
                try:
                    self.price_limit = int(text.upper()[2:])
                    push_instance.logger_instance.info(f"Price limit set to {self.price_limit}")
                    push_instance.push(f"Price limit set to {self.price_limit}")
                    self.search_listings()
                except Exception as ex:
                    print(f"Exception in self.price_limit: {ex}")
            else:
                print(f"Number not provided. Score price limit remains at {self.price_limit}")
        elif text.upper() == "RL":
            self.report_listings()
        elif text.upper() == "SL":
            self.search_listings()
        elif text.upper() == "DEBUG ON":
            self.debug = True
        elif text.upper() == "DEBUG OFF":
            self.debug = False
        elif text.upper() == "PL":
            push_instance.push(f"Price limit is currently {self.price_limit}")
        else:
            print(f"Slack request {text.upper()} not recognized in process_slack_text")
            push_instance.push(f"Slack request {text.upper()} not recognized in process_slack_text")

    def search_loop(self):
        while True:
            self.search_listings()
            tools.sleep_phase(sleep_total=self.loop_sleep, sleep_interval=self.loop_sleep_interval)


def search_start():
    url = ("https://www.stubhub.com/los-angeles-kings-los-angeles-tickets-1-20-2024/event/"
           "151887329/?quantity=2&estimatedFees=true&listingQty=&sections=1133534%2C"
           "1133540%2C1133543%2C1133539%2C1133538%2C1133544%2C1133545%2C1133529%2C"
           "1133536%2C1133528%2C1133535%2C1133533%2C1133541%2C1133532%2C1133542%2C"
           "1133341%2C1133336%2C1133339%2C1133346%2C1133344%2C1133340%2C1133527%2C"
           "1504157%2C1505140%2C1504511%2C1504155%2C1504159%2C1504513%2C1504519%2C"
           "1505139%2C1504154%2C1504523%2C1504521%2C1504158%2C1504530%2C1504515%2C"
           "1133342&ticketClasses=2432%2C4741%2C5105%2C5107%2C5211%2C5307&rows=&seatTypes=")

    search = TicketSearch(url, name="Kings", price_limit=230, loop_sleep=120, debug=False)
    if search.debug:
        print(url)
    read_slack_thread = threading.Thread(target=search.slack_thread)
    read_slack_thread.start()
    search.search_loop()


def main():
    search_thread = threading.Thread(target=search_start)
    search_thread.start()


if __name__ == "__main__":
    main()
