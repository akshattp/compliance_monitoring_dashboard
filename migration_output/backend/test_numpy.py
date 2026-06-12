import numpy as np
import math

def clean_dict_for_json(d):
    if isinstance(d, dict):
        return {k: clean_dict_for_json(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [clean_dict_for_json(v) for v in d]
    elif isinstance(d, (np.int64, np.int32, np.int16, np.int8)):
        return int(d)
    elif isinstance(d, (np.float64, np.float32, np.float16)):
        if np.isnan(d) or np.isinf(d):
            return 0.0
        return float(d)
    elif isinstance(d, float):
        if math.isnan(d) or math.isinf(d):
            return 0.0
    return d

test_data = {"a": np.int64(1), "b": [np.float64(np.nan)], "c": np.float64(1.23)}
print(clean_dict_for_json(test_data))
