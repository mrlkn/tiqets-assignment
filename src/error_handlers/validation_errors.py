import sys


class TiqetsProcessorLoggedError:
    """
    Base logged error class for Tiqets Processor
    """

    def __init__(self, message):
        self.message = message
        print(f"{self.__class__.__name__}: {message}", file=sys.stderr)


class InvalidOrderDataError(TiqetsProcessorLoggedError):
    """
    Logged error for invalid order data
    """

    pass


class InvalidBarcodeDataError(TiqetsProcessorLoggedError):
    """
    Logged error for invalid barcode data
    """

    pass


class DuplicateBarcodeError(TiqetsProcessorLoggedError):
    """
    Logged error for duplicate barcode
    """

    pass


class OrderWithoutBarcodesError(TiqetsProcessorLoggedError):
    """
    Logged error for order without associated barcodes
    """

    pass
