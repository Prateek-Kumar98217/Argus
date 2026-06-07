#centralize custom exceptions


#GraphState related exceptions
class GraphStateError(Exception):
    pass

class NotInitializedError(GraphStateError):
    pass

class NodeConflictError(GraphStateError):
    pass

#Retriever related exceptions

class RetrieverError(Exception):
    pass

class NoContextError(RetrieverError):
    pass