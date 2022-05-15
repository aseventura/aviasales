import argparse
import json
import operator

import dateutil.parser
from lxml import etree
from deepdiff import DeepDiff


def parse_flight_info(flight) -> dict:
    flight_information = {}
    for tag in flight.getchildren():
        if not tag.text is None:
            flight_information[tag.tag] = tag.text.strip()
    return flight_information


def get_flight_price(pricing: list) -> float:
    flight_price = 0.0
    for service_charges in pricing:
        if 'TotalAmount' in service_charges.values():
            flight_price += float(service_charges.text)
    return flight_price


def is_itinerary_dxb_to_bkk(source_city: str, destination_city: str, itinerary: list) -> bool:
    if itinerary[0]['Source'] == source_city and itinerary[-1]['Destination'] == destination_city:
        return True
    else:
        return False


def get_time_to_flying(itinerary: list):
    departure_time_stamp = dateutil.parser.isoparse(itinerary[0]['DepartureTimeStamp'])
    arrival_time_stamp = dateutil.parser.isoparse(itinerary[-1]['ArrivalTimeStamp'])
    return int((arrival_time_stamp - departure_time_stamp).total_seconds())


def find_all_flights_from_dxb_to_bkk(xml_response):
    xml_tree = etree.parse(xml_response)
    root_tag = xml_tree.getroot()
    source_city = 'DXB'
    destination_city = 'BKK'
    find_flights = []
    for flights in root_tag.xpath('PricedItineraries/Flights'):
        dxb_to_bkk = {}
        current_itinerary = []
        for one_flight in flights.xpath('OnwardPricedItinerary/Flights/Flight'):
            current_itinerary.append(parse_flight_info(one_flight))
        if is_itinerary_dxb_to_bkk(source_city, destination_city, current_itinerary):
            dxb_to_bkk['itinerary'] = current_itinerary
            dxb_to_bkk['time_to_flying'] = get_time_to_flying(current_itinerary)
            dxb_to_bkk['price'] = get_flight_price(flights.xpath('Pricing/ServiceCharges'))
            find_flights.append((dxb_to_bkk))
    return find_flights


def search_updated_flight_information(all_flights: list):
    pass


def get_parse_params():
    parser = argparse.ArgumentParser(
        description='Программа поиска полётов по заданным критериям: вывод всех полётов, их продолжительность, цена.'
    )
    parser.add_argument('--showall', help='Вывод всех найденных рейсов', action='store_true')
    parser.add_argument('--maxprice', help='Вывод самого дорогого рейса', action='store_true')
    parser.add_argument('--minprice', help='Вывод самого дешёвого рейса', action='store_true')
    parser.add_argument('--mintime', help='Вывод самого быстрого рейса', action='store_true')
    parser.add_argument('--maxtime', help='Вывод самого долгого рейса', action='store_true')
    return parser.parse_args()


def main():
    aggregators_filename = ('RS_Via-3.xml', 'RS_ViaOW.xml')
    all_flights = []
    for aggregator in aggregators_filename:
        all_flights += find_all_flights_from_dxb_to_bkk(aggregator)

    cli_params = get_parse_params()
    if cli_params.showall:
        print('Вывод всех рейсов:')
        print(json.dumps(all_flights, indent=4, ensure_ascii=False))
    elif cli_params.maxprice:
        print('Самый дорогой билет:')
        print(json.dumps(max(all_flights, key=operator.itemgetter('price'))))
    elif cli_params.minprice:
        print('Самый дешёвый билет:')
        print(json.dumps(min(all_flights, key=operator.itemgetter('price'))))
    elif cli_params.mintime:
        print('Самый быстрый билет:')
        print(json.dumps(min(all_flights, key=operator.itemgetter('time_to_flying'))))
    elif cli_params.maxtime:
        print('Самый долгий билет:')
        print(json.dumps(max(all_flights, key=operator.itemgetter('time_to_flying'))))


if __name__ == '__main__':
    main()
