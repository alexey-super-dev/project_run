

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
