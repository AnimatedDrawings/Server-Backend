TORCHSERVE_URL = "http://torchserve:8080/predictions/drawn_humanoid_detector"


IMAGE_SHAPE_ERROR = "image must have 3 channels (rgb). Found {len_shape}"
SEND_TO_TORCHSERVE_ERROR = "Failed to get bounding box, please check if the 'docker_torchserve' is running and healthy, resp: {resp}"
DETECTION_ERROR = "Error performing detection. Check that drawn_humanoid_detector.mar was properly downloaded. Response: {detection_results}"
NO_DETECTION_ERROR = "Could not detect any drawn humanoids in the image. Aborting"
REPORT_HIGHEST_SCORE_DETECTION = (
    "Detected {count} humanoids in image. Using detection with highest score {score}."
)
CALCULATE_BOUNDING_BOX_ERROR = "Error calculating bounding box. Error: {error}"
