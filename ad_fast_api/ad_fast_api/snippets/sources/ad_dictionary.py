from typing import Optional, TypeVar, List, Dict, Any


K = TypeVar("K")


def get_value_from_dict(
    key_list: List[K],
    from_dict: Optional[Dict[K, Any]],
) -> Optional[Any]:
    try:
        if from_dict is None:
            return None

        if not key_list:
            return None

        tmp_value = from_dict.get(key_list[0])
        for i in range(1, len(key_list)):
            if tmp_value is None:
                return None
            tmp_value = tmp_value.get(key_list[i])
        return tmp_value
    except:
        return None
