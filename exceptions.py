class DatabaseException(Exception):
    def __init__(self, message="A database error occurred."):
        super().__init__(message)


class RecordNotFoundException(DatabaseException):
    def __init__(self, message="Record not found."):
        super().__init__(message)


class DuplicateRecordException(DatabaseException):
    def __init__(self, message="Record already exists."):
        super().__init__(message)


class DatabaseConnectionException(DatabaseException):
    def __init__(self, message="Could not connect to the database."):
        super().__init__(message)


class DatabaseOperationException(DatabaseException):
    def __init__(self, message="A database operation failed."):
        super().__init__(message)
