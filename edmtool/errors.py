class MissingArgumentsError(Exception):
    pass


class ServerError(Exception):
    pass


class ProcessInterruptedError(Exception):
    pass


class DifferentFileSizeError(Exception):
    pass


class UploadDoNotExistError(Exception):
    pass


class EncodedFileExistsError(Exception):
    pass


class DifferentCellsInTheRowError(Exception):
    pass


class CellIsEmptyError(Exception):
    pass
