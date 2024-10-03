from modules import tools, push

push_instance = push.Push(calling_function="TicketSearch")

# package imports
import datetime
import json
import requests
from bs4 import BeautifulSoup
import threading
import time


class TicketSearch:

    def __init__(self, url=None, name="No name given", gamedate=None, debug=False,
                 price_limit=250, upper_level_price_limit=100, loop_sleep=120):
        self.gamedate = gamedate
        if url is None:
            self.set_event_text(name, gamedate)
        self.listing_name = name
        self.debug = debug
        self.listings = dict()
        self.current_listings = list()
        self.found_listings = list()
        self.upper_level_price_limit = upper_level_price_limit
        self.price_limit = price_limit
        self.loop_sleep = loop_sleep
        self.loop_sleep_interval = 10
        self.min_price = 1000

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

    def set_event_text(self, venue, gamedate):

        event_id = ""
        sections = ""
        event_text = ""
        if venue == "Padres":
            event_text = "san-diego-padres-san-diego-tickets"
            sections = f"780084%2C780039%2C780049%2C780045%2C780040%2C780063%2C780050%2C" \
                       "780066%2C780048%2C780065%2C780043%2C1905537%2C780042%2C780083%2C780052%2C780053%2C" \
                       "1473671%2C780038%2C780060%2C780047%2C780032%2C780087%2C1473673%2C780107%2C780055%2C" \
                       "780044%2C780082%2C780062%2C1473665%2C780076%2C780073%2C780041%2C780072%2C780077%2C" \
                       "780074%2C1476124%2C780067%2C780054%2C780051%2C780080%2C780086%2C1476122%2C780046%2C" \
                       "780088%2C780058%2C1473675%2C780056%2C780068%2C780036%2C780035%2C780109%2C780113%2C" \
                       "780059%2C1473667%2C780064%2C780075%2C1473669%2C780037%2C780069%2C780090%2C780071%2C" \
                       "780078%2C780061%2C1473677%2C1476538%2C1476127%2C780033%2C780070%2C780110%2C780111%2C" \
                       "1476534%2C780085%2C1476536%2C780057%2C780104%2C1476532%2C1713145%2C780081%2C780108" \
                       "&ticketClasses=3832%2C3893%2C3361%2C4021%2C4029%2C3852%2C4099%2C21727%2C4009%2C1807%2C" \
                       "3493%2C9026%2C3543%2C1745%2C1767%2C4749%2C4066%2C4028"
            if gamedate == "10-1-2024":
                event_id = 154103620
            else:
                event_id = 154103615
        elif venue == "Kings":
            event_text = "los-angeles-kings-los-angeles-tickets"
            sections = f"1133534%2C" \
                       "1133540%2C1133543%2C1133539%2C1133538%2C1133544%2C1133545%2C1133529%2C" \
                       "1133536%2C1133528%2C1133535%2C1133533%2C1133541%2C1133532%2C1133542%2C" \
                       "1133341%2C1133336%2C1133339%2C1133346%2C1133344%2C1133340%2C1133527%2C" \
                       "1504157%2C1505140%2C1504511%2C1504155%2C1504159%2C1504513%2C1504519%2C" \
                       "1505139%2C1504154%2C1504523%2C1504521%2C1504158%2C1504530%2C1504515%2C" \
                       "1133342&ticketClasses=2432%2C4741%2C5105%2C5107%2C5211%2C5307"

        self.url = (f"https://www.stubhub.com/{event_text}-{gamedate}/event/{event_id}/"
                    f"?quantity=2&sections={sections}&rows=&seats=&seatTypes=&listingQty=")

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
                    (price <= price_limit and section_header != "3" and row != "GA" and row != "44D") or
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
                    self.min_price = min(self.min_price, price)
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
        else:
            self.price_limit = self.min_price + 5
            print(f"New limit is {self.price_limit}")
            push_instance.push(f"New limit is {self.price_limit}", title="Tickets")

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
        if len(self.listings) > 0:
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

    def search_start(self):
        if self.debug:
            print(self.url)
        push_instance.push(f"\n\nNew search ({self.listing_name}) started\n\n")
        search_thread = threading.Thread(target=self.search_loop)
        search_thread.start()
        read_slack_thread = threading.Thread(target=self.slack_thread)
        read_slack_thread.start()


def main():
    url = ("https://www.stubhub.com/los-angeles-kings-los-angeles-tickets-1-20-2024/event/"
           "151887329/?quantity=2&estimatedFees=true&listingQty=&sections=1133534%2C"
           "1133540%2C1133543%2C1133539%2C1133538%2C1133544%2C1133545%2C1133529%2C"
           "1133536%2C1133528%2C1133535%2C1133533%2C1133541%2C1133532%2C1133542%2C"
           "1133341%2C1133336%2C1133339%2C1133346%2C1133344%2C1133340%2C1133527%2C"
           "1504157%2C1505140%2C1504511%2C1504155%2C1504159%2C1504513%2C1504519%2C"
           "1505139%2C1504154%2C1504523%2C1504521%2C1504158%2C1504530%2C1504515%2C"
           "1133342&ticketClasses=2432%2C4741%2C5105%2C5107%2C5211%2C5307&rows=&seatTypes=")
    search = TicketSearch(url, name="Kings", price_limit=230, loop_sleep=120, debug=False)
    search.search_start()


if __name__ == "__main__":
    main()
