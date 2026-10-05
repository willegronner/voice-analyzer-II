class InvalidIdentifierError(ValueError):
    def __init__(self, field, value, expected_format):
        self.field = field
        self.value = value
        self.reason = f"'{value}' does not match the format {expected_format}"
        super().__init__(self.reason)


class InvalidRecordError(ValueError):
    def __init__(self, field, reason):
        self.field = field
        self.reason = reason
        super().__init__(f"{field}: {reason}")


class DataFileError(Exception):
    def __init__(self, path, reason):
        self.path = path
        self.reason = reason
        super().__init__(f"{path}: {reason}")
