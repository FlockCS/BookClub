from redis import Redis, RedisError
import os
from datetime import datetime, timezone, date
from typing import Any
import json

# getting redis client
cache_endpoint = os.environ["ELASTICACHE_CLUSTER_ENDPOINT"]
cache_port = 6379
redis_client = Redis(
    host=cache_endpoint, 
    port=cache_port, 
    decode_responses=True
)
print(f"connection to redis client: {redis_client.ping()}")

def cache_put(key: str, value: Any) -> bool:
    """
    Put item into Elasticache cluster

    input:
        key: str -> key for the item
        value: Any -> item to cache; needs to be JSON serializable
    
    returns:
        True if item cached, False if not

    raises:
        Exception: Value cannot be decoded into a JSON string
                   or Redis put action failed
    """
    try:
        dumped_value = json.dumps(value)
        redis_client.set(
            name=key, 
            value=dumped_value, 
            ex=15*60 # 15 min ttl, reduce if needed
        )

        print(f"succesfully added key={key}, value={value} to cache.")
    except TypeError as e:
        msg = f"Failed to serialize value {value}. Make sure value is a JSON serializable object."
        raise Exception(msg)
    except RedisError as e:
        msg = f"Failed redis put action. {e}"
        raise Exception(msg)

def cache_get(key: str) -> Any:
    """
    Get a cached item from redis

    input:
        key: str -> key for the item

    returns:
        Object: Any -> stored object from cache

    raises:
        Exception -> JSON object retrieved from redis cannot be converted into dict
    """
    try:
        dumped_value = redis_client.get(key)
        value = json.loads(dumped_value)

        print(f"successfully retrieved value for key {key}")
        return value
    except json.JSONDecodeError as e:
        msg = f"Error with decoding json value."
        raise Exception(msg)