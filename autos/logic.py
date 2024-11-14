import requests

from autos.models import Position


def calculate_run_time_by_id(run):
    from autos.models import Position

    # Get the first and last Position objects by id
    first_position = Position.objects.filter(run=run).order_by('id').first()
    last_position = Position.objects.filter(run=run).order_by('id').last()

    if first_position and last_position:
        # Ensure both positions have a valid date_time
        if first_position.date_time and last_position.date_time:
            # Calculate the time difference
            time_difference = last_position.date_time - first_position.date_time
            run_time_seconds = time_difference.total_seconds()
        else:
            run_time_seconds = 0  # Handle case where date_times might be null
    else:
        run_time_seconds = 0  # Handle case with no positions

    return run_time_seconds


from django.db.models import Min, Max


def calculate_run_time(run):
    from autos.models import Position

    positions = Position.objects.filter(run=run)

    # Get the earliest and latest date_time for the given run
    date_time_min = positions.aggregate(Min('date_time'))['date_time__min']
    date_time_max = positions.aggregate(Max('date_time'))['date_time__max']

    if date_time_min and date_time_max:
        # Calculate the time difference
        time_difference = date_time_max - date_time_min
        run_time_seconds = time_difference.total_seconds()
    else:
        run_time_seconds = 0  # or handle this case as required

    return run_time_seconds


def calculate_run_time_different_way(run):
    positions_qs = Position.objects.filter(run=run.id)
    positions_quantity = len(positions_qs)
    positions_qs_sorted_by_date = positions_qs.order_by('date_time')

    run_time = positions_qs_sorted_by_date[positions_quantity - 1].date_time - positions_qs_sorted_by_date[0].date_time
    return run_time.total_seconds()


def calculate_median(numbers):
    return sum(numbers) / len(numbers)


class CarbonInterfaceError(Exception):
    pass


# Your API key
def call_carboninterface(key, distance):
    # Endpoint for estimating vehicle emissions
    # url = 'https://dog.ceo/api/breeds/image/random'
    url = 'https://www.carboninterface.com/api/v1/estimates'

    # Headers with API key
    headers = {
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'
    }

    # Data for the request (example for a vehicle emission estimate)
    data = {
        'type': 'vehicle',
        'distance_unit': 'km',
        'distance_value': distance,
        'vehicle_model_id': '7268a9b7-17e8-4c8d-acca-57059252afe9'
    }

    # Make the POST request
    response = requests.post(url, headers=headers, json=data)

    # Check the response
    if response.status_code in [200, 201]:
        # Parse the JSON response
        result = response.json()
        try:
            return int(result['data']['attributes']['carbon_g'])
        except (KeyError, ValueError):
            raise CarbonInterfaceError(str(result))
    else:
        raise CarbonInterfaceError
