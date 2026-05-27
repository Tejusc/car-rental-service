class CarNotFoundError(Exception):
    def __init__(self, car_id):
        self.car_id = car_id


class CarNotAvailableError(Exception):
    def __init__(self, car_id):
        self.car_id = car_id


class CarNotRentedError(Exception):
    def __init__(self, car_id):
        self.car_id = car_id
