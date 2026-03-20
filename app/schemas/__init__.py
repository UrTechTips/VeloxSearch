from .apikeys_schema import schema as apikey_schema
from .datasets_schema import schema as dataset_schema
from .feedback_schema import schema as feedback_schema
from .usage_schema import schema as usage_schema
from .user_schema import schema as user_schema

all_schemas = {
    "dataset": dataset_schema,
    "user": user_schema,
    "apikey": apikey_schema,
    "usage": usage_schema,
    "feedback": feedback_schema
}