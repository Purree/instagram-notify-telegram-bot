# Class may contain only static methods
class FunctionResult:
    isSuccess = False
    returnValue = []
    errorMessage = ''

    def __init__(self):
        pass

    @staticmethod
    def success(return_value=None):
        result = FunctionResult()
        result.isSuccess = True
        result.returnValue = return_value
        return result

    @staticmethod
    def error(error_message):
        result = FunctionResult()
        result.isSuccess = False
        result.errorMessage = error_message
        return result
